# PMU counter observation schema — offline only

Four unittest cases PASS: exact version/nonce/eight-sample ordering; unsigned
values; rejection of WO/unreviewed addresses; rollover aliasing controls.
Only PIT0..3_COUNTER (0xffd40044/54/64/74) are accepted in two ordered rounds.
No hardware capture or physical backend is provided. Supplied records are not
authenticated hardware evidence; a nonce is only a caller correlation check.

The decoder reports raw values and changed/unchanged. Samples are sequential,
not atomic. Equal endpoints can represent a stopped counter or whole periods;
changed endpoints also cannot determine wrap count. Reload, enable, prescaler,
clock frequency and ownership are unknown. No elapsed-time/deadline inference
or destructive DDR admission follows. GPO0/preload remain write-only; control
fields remain excluded pending review. No register read/write occurred.

Reproduce: `python -m unittest discover -s tests -p test_pit_counter_observation.py -v`.
Next: offline bounded callback/read-failure contract and PMU-local capture design;
physical integration requires a new reviewed image and restoration admission.
