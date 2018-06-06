# Antibiotics RCT

This repository holds the code, data and documentation for our RCT
*The Effect of Audit & Feedback on Prescribing Behaviour and
Engagement with Data on OpenPrescribing.net - A Randomised Controlled
Trial Protocol*.

This is a cluster-randomised, controlled parallel-group
trial. Participants will be allocated to intervention or control group
in a 1:1 ratio, block-randomised by CCG. Those in the intervention
group will be allocated to receive one of two different styles of
intervention (which we call `A` or `B`), block-randomised by CCG.

Intervention `A` varies the content of the email on each wave. `B` is
the same on each wave, but with fresh data each time. Examples are
given in the "intervention" PDFs found in the protocol folder.

Practices will receive three waves of communications over three
months, on 2018-05-07, 2018-06-11, and 2018-07-16.

All recipients will receive an email, a letter, and a fax.  The
message they receive will include a link which is coded to include
variables for tracking the intervention and the wave (see #2).x

We are seeking to investigate superiority of any intervention over
control, and to explore the relative impact of different
interventions.


## Software

The software for generating and sending interventions is a Django app in the `antibioticsrct` subfolder. See the `README.md` there for further details.
