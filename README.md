# Nimodipine cohort study

This repository holds the code, data and documentation for our cohort
study *The Effect of Audit & Feedback on Prescribing Behaviour and
Engagement with Data on OpenPrescribing.net - A Programme of
Randomised Controlled Trials and Cohort Studies* (Med IDREC Ref: ​
R55595/RE001). The protocol is at `docs/protocol/protocol.pdf`.

This is a cohort study.  All practices in the cohort receive the
intervention.  The intervention alerts pratices to potentially
dangerous prescribing patterns relating to the drug nimodipine.

All recipients will receive an email, a letter, and a fax.  The
message they receive will include a link which is coded to include
variables for tracking the intervention and the wave.

Outcomes are:

* P1: does receipt of audit feedback prompt an improvement in performance
* S1: is email, letter or fax most effective

These will be measured via Google Analytics with comparison to each
other and earlier control periods.  A follow-up letter will be sent
6-12 months after the end of the trial.

We also ask a simple feedback question "Did the message we sent give
you new information about your prescribing?" when someone follows a
link from a letter.


## Software

This software started as a clone of
https://github.com/ebmdatalab/antibiotics-rct/, which was an RCT about
antibiotics prescribing.

The code for generating and sending interventions is a Django app
in the `nimodipine-web` subfolder. See the `README.md` there for
further details.
