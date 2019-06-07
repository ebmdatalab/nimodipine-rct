import base64
from io import BytesIO
import logging
import os
import tempfile

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from django.conf import settings
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.safestring import SafeText
from django.views.decorators.csrf import csrf_exempt

from nimodipine.models import Intervention

logger = logging.getLogger(__name__)


@csrf_exempt
def fax_receipt(request):
    if request.method == 'POST':
        # https://www.interfax.net/en/dev/dev-guide/receive-sent-fax-confirmations-via-callback
        recipient = request.POST.get('DestinationFax')
        subject = request.POST.get('Subject', '')
        status = request.POST.get('Status', '')
        logger.info(
            "Received fax callback: to <%s>, subject <%s>, status <%s>",
            recipient, subject, status)
        if recipient:
            # It is possible for more than one survey to share a fax machine
            interventions = Intervention.objects.filter(
                contact__normalised_fax=recipient, method='f')
            ids = [x.pk for x in interventions]
            if len(ids) == 0:
                raise Http404()
            if status == '0':
                interventions.update(receipt=True)
                logger.info("Intervention %s marked as received", ids)
            elif int(status) > 0:
                interventions.update(receipt=False)
                logger.warn(
                    "Problem sending fax for intervention %s (status %s)",
                    ids,
                    status)
            else:
                logger.info(
                    "Received temporary fax status for intervention %s (status %s)",
                    ids,
                    status)
        else:
            logger.warn("Unable to parse intervention")
        return HttpResponse('OK')


def measure_redirect(request, method, practice_id):
    intervention = Intervention.objects.get(
        method=method, practice_id=practice_id)
    if request.POST:
        # The user has filled out the one-off interstitial
        # questionnaire
        if request.POST['survey_response'].lower() == 'yes':
            intervention.contact.survey_response = True
        elif request.POST['survey_response'].lower() == 'no':
            intervention.contact.survey_response = False
        intervention.contact.save()
    else:
        intervention.hits += 1
        intervention.save()
        if intervention.contact.total_hits() == 1:
            return render(
                request, 'questionnaire.html')
    return redirect(intervention.get_target_url())


def intervention_message(request, intervention_id):
    intervention = get_object_or_404(Intervention, pk=intervention_id)
    practice_name = intervention.contact.cased_name
    context = {}
    show_header_from = True
    if intervention.method == 'p':
        show_header_to = True
    else:
        show_header_to = False
    template = 'intervention.html'
    encoded_image = make_chart(intervention.metadata['value'])
    with open(os.path.join(
            settings.BASE_DIR,
            'nimodipine',
            'static',
            'header.png'), 'rb') as img:
        header_image = base64.b64encode(img.read()).decode('ascii')
    with open(os.path.join(settings.BASE_DIR, 'nimodipine', 'static',  'footer.png'), 'rb') as img:
        footer_image = base64.b64encode(img.read()).decode('ascii')
    intervention_url = "op2.org.uk{}".format(intervention.get_absolute_url())
    intervention_url = '<a href="http://{}">{}</a>'.format(
        intervention_url, intervention_url)
    context.update({
        'intervention': intervention,
        'practice_name': practice_name,
        'intervention_url': SafeText(intervention_url),
        'encoded_image': encoded_image,
        'header_image': header_image,
        'footer_image': footer_image,
        'show_header_from': show_header_from,
        'show_header_to': show_header_to
    })
    return render(
        request,
        template,
        context=context)


def make_chart(practice_value):
    """Draw lines on a pre-made chart pointing to a peak (always in the
    same place), and a point on the axis (variable).

    Args:
       practice_value: numeric value that will be plotted on x-axis

    Returns:
       base64-encoded image

    """
    # set up chart, dimensions
    base_image_path = os.path.join(
        settings.BASE_DIR,
        'nimodipine',
        'static',
        'chart.png')
    im = Image.open(base_image_path)
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype('arial.ttf', 14)
    except OSError:  # font not installed
        try:
            # Use Free version of Arial
            fnt = ImageFont.truetype('LiberationSans-Regular.ttf', 14)
        except OSError:
            # fallback to anything
            logger.warn("Falling back to default font for drawing charts")
            fnt = ImageFont.load_default()

    blue_text = "97% of practices \n(0 tablets per 1000 patients)"
    red_text = "Your practice\n({} tablets per 1000 patients)".format(
        practice_value)
    x_axis_origin_coords = (51,   226)
    x_axis_end_coords = (364, 226)
    x_axis_width = x_axis_end_coords[0] - x_axis_origin_coords[0]
    x_axis_max = 80  # The value at the extreme end of X-axis
    blue_line_coords = (60, 30)  # coords of pointer to the peak in the chart

    practice_x = x_axis_origin_coords[0] + int((float(practice_value) / x_axis_max * x_axis_width))
    practice_coords = (practice_x, x_axis_origin_coords[1])
    # Arrived at by trial-and-error, so red text never overflows right edge of chart:
    red_text_max_x = 170
    red_text_min_x = blue_line_coords[0]

    def arrow(d, arrow_end, feather_end, fill="red", width=1):
        if arrow_end[0] == feather_end[0]:
            orientation = "vertical"
        elif arrow_end[1] == feather_end[1]:
            orientation = "horizontal"
        else:
            raise BaseException("Must be horizontal or vertical")

        d.line((arrow_end, feather_end), fill=fill, width=width)
        if orientation == "vertical":
            d.line((arrow_end, (arrow_end[0]-5, arrow_end[1]-5)), fill=fill, width=width)
            d.line((arrow_end, (arrow_end[0]+5, arrow_end[1]-5)), fill=fill, width=width)
        else:
            d.line((arrow_end, (arrow_end[0]+5, arrow_end[1]-5)), fill=fill, width=width)
            d.line((arrow_end, (arrow_end[0]+5, arrow_end[1]+5)), fill=fill, width=width)

    # Draw line pointing at peak
    blue_line_feather_end_coords = (blue_line_coords[0] + 60, blue_line_coords[1])
    blue_text_coords = (blue_line_feather_end_coords[0] + 5, blue_line_feather_end_coords[1] - 6)
    arrow(d, blue_line_coords, blue_line_feather_end_coords, fill="blue")
    d.text(blue_text_coords, blue_text, font=fnt, fill="blue")

    # Draw line pointing at practice
    red_line_feather_end_coords = (practice_coords[0], practice_coords[1]-25)
    red_text_x = red_line_feather_end_coords[0]-20
    if red_text_x < red_text_min_x:
        red_text_x = red_text_min_x
    elif red_text_x > red_text_max_x:
        red_text_x = red_text_max_x
    red_text_coords = (red_text_x, red_line_feather_end_coords[1]-40)
    arrow(d, practice_coords, red_line_feather_end_coords)
    d.text(red_text_coords, red_text, font=fnt, fill="red")

    # Render image to base64-encoding
    mock_file = BytesIO()
    im.save(mock_file, 'png')
    mock_file.seek(0)
    return base64.b64encode(mock_file.read()).decode('ascii')
