This is a Django application to track interventions in our Antibiotics RCT.

Each intervention is to a single practice, either by fax, post, or
email. All practices get all three eventually, in random orders, 1 of
each over 3 months.

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

* generate skeleton interventions based on an allocation spreadsheet
  (run once only at the start of the RCT) (`create_interventions`)

* generate letters for each intervention (e.g. all postal letters for
  wave 1) (`generate_wave`)

* send the email and fax letters via third party services
  (`send_messages`)

* generate 2 report CSVs: one describing the sending and receipt of
  intervention letters, and the other describing the results of the
  interstitial questionnaire (`generate_report`)

# Typical workflow

Set up the Django app (`pip install` etc; there is a `fabfile` for
deploying to our pet server, and a `environment-sample` file that
should be sourced before running

Create interventions (once only at start of RCT). The allocation CSV is
generated from the jupyter notebook in the same folder.  The contacts
CSV is a download of a tab of [this Google Sheet](https://docs.google.com/spreadsheets/d/1iVtlo-qGaK9KT35FaX94Gu0azei-TLIZZI52TZWvxMg).

    python manage.py create_interventions --allocations=../allocation\ and\ analysis/practice_allocations.csv  --contacts=../allocation\ and\ analysis/practices.csv

Once at the start of each wave (as soon as possible following a
monthly import to OpenPrescribing), create all the letters for that
wave:

    python manage.py generate_wave --wave=1

When a wave has been generated, archive it in github. On `largeweb2` it's in `/mnt/database/antibiotics-rct-data/` -- you can just do a `git commit -am "wave <n> letters" && git push`


When the postal letters have been sent, manually mark them as such:

    Intervention.objects.filter(wave='1', method='p').update(sent=True)

Send the faxes and emails:

    python manage.py send_messages --wave=1 --method=email
    python manage.py send_messages --wave=1 --method=fax


## Other notes

* Generating wave 3 for intervention A requires custom wording, which is inserted in the view. This is in a CSV in the source code, which was downloaded from [this Google Sheet](https://docs.google.com/spreadsheets/d/1Yx9_dWnjscN6FNfes5Q3LT2E2yRdYbQVOY1Q-aZRFQw/edit?usp=drive_web&ouid=112987570757514537466)
* Mailgun setup for fax - add a route `match_recipient("fax@openprescribing.net") -> forward("http://op2.org.uk/fax_receipt")`
