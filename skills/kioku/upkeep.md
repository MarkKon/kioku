# Upkeep

`kioku upkeep` is meant to run daily, for example as a scheduled task. It
checks the model, commits it to the model folder's git repo (and pushes when it
has a remote), lists likely duplicates and areas worth splitting (over about
40 ideas, or a cluster of ideas linked only to each other), and shows how well
the learner's confidence digits are calibrated. `kioku upkeep --check` only
checks, and exits 1 on a problem.

**Notes folder.** When `vault` is set in `config.toml`, upkeep lists finished
notes that have no idea yet. With `--scout` and a configured `scout_model`, a
cheap model drafts ideas for them into `proposals.md`. When the learner
approves drafts, check each against its note, add it with `kioku add`, and end
its `##` header in `proposals.md` with `· added` or `· skipped`. Notes are
hints for what to add, never evidence.

**An area worth splitting**: move a cluster of its ideas into a new sub-area
with `kioku edit a,b,c --area <area>/<new> --new-area`.
