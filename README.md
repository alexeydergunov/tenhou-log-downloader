Prerequisites:

- download [mjlog2json](https://github.com/tsubakisakura/mjlog2json) to a sibling directory (so that mjlog2json and tenhou-log-downloader lie in the same directory)
- download Rust and build mjlog2json: `cargo build -r`
- create venv: `python3 -m venv ./venv`
- install requirements: `./venv/bin/pip3 install -r requirements.txt`

Usage:

- `./main.py -i [input_file] -o [output_dir] [--fix-scores]`
- `./main.py -u [url] -o [output_dir] [--fix-scores]`

Parameters description:

- You need to specify exactly one of `-i`, `-u`. If `-u` is set, it will download a single log `[url]`. If `-i` is set, it will download all logs contained in file `[input_file]`, one url at a line.
- Parameter `-o` is a directory where the logs are downloaded to. First XML logs are downloaded to `[output_dir]/xml`, then they are converted by mjlog2json to `[output_dir]/json`.
- Use option `--fix-scores` if you are playing with tournament rules without busting. It modified scores in each hand so that the scores are not negative and the sum is 100000. This is to put logs to Mortal reviewer https://mjai.ekyu.moe/ as Custom log.
