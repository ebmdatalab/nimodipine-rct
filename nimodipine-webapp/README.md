This is a Django application to track interventions in our nimodipine
study.

Each intervention is to a single practice, by fax, post, and
email. All practices get all three contact methods.

The intervention takes the form of a letter telling them hopefully
interesting things, with a URL for them to follow.

The URL is a short url which encodes the intervention in a readable /
copyable form.

When a practice follows any of these URLs for the first time, it is presented
an interstitial page with a simple yes/no questionnaire, the answer to
which is recorded in our app.

They are then redirected to their page on the main OpenPrescribing
website, along with Google Analytics tracking tags.

There are management scripts to :

* generate skeleton interventions based on a contact spreadsheet
  (run once only at the start of the study) (`create_interventions`)

* generate communication for each intervention (i.e. all postal
  letters, all emails, all faxes) (`generate_wave`)

* send the email and fax letters via third party services
  (`send_messages`)

* generate 2 report CSVs: one describing the sending and receipt of
  intervention letters, and the other describing the results of the
  interstitial questionnaire (`generate_report`)

# Typical workflow

Set up the Django app (`pip install` etc; there is a `fabfile` for
deploying to our pet server, and a `environment-sample` file that
should be sourced before running

Create interventions (once only at start of the study). The practices to
contact are generated based on practices with persistent and recent
(if low-level) nimodipine prescribing, using a notebook in this
repository.  This is used to create a spreadsheet of contacts which
should be committed to this repository when generated for the study.
The spreadsheet must be in the format described in #2.  Interventions
for post, email and fax are then generated thus:

    python manage.py create_interventions --contacts=../allocation\ and\ analysis/practices.csv

Then pre-generate files for each of the contact methods for review:

    python manage.py generate_wave --method=p
    python manage.py generate_wave --method=f
    python manage.py generate_wave --method=e

When a wave has been generated, archive it in this repository.

When the postal letters have been sent, manually mark them as such:

    Intervention.objects.filter(wave='1', method='p').update(sent=True)

Sending the faxes and emails automatically handings them being marked as set:

    python manage.py send_messages --wave=1 --method=email
    python manage.py send_messages --wave=1 --method=fax


## Other notes
* In order to facilitate integration with openprescribing, the app connects to (and creates tables in) the existing openprescribing database. This already has a MailLog model, so there is a warty migration (`0003_maillog.py` which is only run in test/dev environments)
* Mailgun setup for fax - add a route `match_recipient("fax@openprescribing.net") -> forward("http://op2.org.uk/fax_receipt")`
