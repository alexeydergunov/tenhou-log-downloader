Prerequisites:

- download [mjlog2json](https://github.com/tsubakisakura/mjlog2json) to a sibling directory (so that mjlog2json and tenhou-log-downloader lie in the same directory)
- (not needed for JSON logs of ranked matches) install Rust and build mjlog2json: `cargo build -r`
- create venv: `python3 -m venv ./venv`
- install requirements: `./venv/bin/pip3 install -r requirements.txt`

Usage:

- `./main.py -i [input_file] -o [output_dir] [--skip-xml] [--fix-scores]`
- `./main.py -u [url] -o [output_dir] [--skip-xml] [--fix-scores]`

You can skip venv creation and use system Python. In this case:

- use `pip3` instead of `./venv/bin/pip3`
- use `python3 main.py` instead of `./main.py`
- on Windows, it could be `pip` and `python` instead of `pip3` and `python3`

Parameters description:

- You need to specify exactly one of `-i`, `-u`. If `-u` is set, it will download a single log `[url]`. If `-i` is set, it will download all logs contained in file `[input_file]`, one url at a line.
- Parameter `-o` is a directory where the logs are downloaded to. First XML logs are downloaded to `[output_dir]/xml`, then they are converted by mjlog2json to `[output_dir]/json`.
- Use `--skip-xml` if you only download ranked matches and only need JSON logs. They can be downloaded directly from Tenhou, so they don't require installing Rust and building mjlog2json.
- Use option `--fix-scores` if you are playing with tournament rules without busting. It modified scores in each hand so that the scores are not negative and the sum is 100000. This is to put logs to Mortal reviewer https://mjai.ekyu.moe/ as Custom log.

Popular examples (probably you need one of them):

- download JSON of a ranked match (doesn't require mjlog2json): `./main.py -u [url] -o [output_dir] --skip-xml`
- download XML and JSON of any match and fix scores (requires mjlog2json): `./main.py -u [url] -o [output_dir] --fix-scores`
