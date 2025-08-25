#!./venv/bin/python3
import json
import logging
import os
import subprocess
from argparse import ArgumentParser
from typing import Optional

import requests

MJLOG2JSON_BINARY_PATH = "../mjlog2json/target/release/mjlog2json"


def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-i", "--input-file")
    arg_parser.add_argument("-u", "--url")
    arg_parser.add_argument("-o", "--output-dir")
    arg_parser.add_argument("-t", "--type", choices=["xml", "json"])
    arg_parser.add_argument("--fix-scores", action="store_true")
    return arg_parser.parse_args()


def get_url_list(args) -> list[str]:
    input_file: Optional[str] = args.input_file
    url: Optional[str] = args.url

    if input_file is None and url is None:
        raise Exception("Must specify at least one of --input-file and --url")
    if input_file is not None and url is not None:
        raise Exception("Cannot use --input-file and --url together")

    urls = []
    if input_file is not None:
        with open(input_file, "r") as f:
            for line in f:
                urls.append(line.strip())
        logging.info("Will download %d urls from file %s", len(urls), input_file)
    else:
        urls.append(url)
        logging.info("Will download one url specified in command line")

    return urls


def get_log_id(url: str) -> str:
    if len(url) < 50:
        raise Exception("Too short url")

    if url.startswith("http://"):
        url = url.replace("http://", "https://")
    if url.startswith("https://tenhou.net/3"):
        url = url.replace("https://tenhou.net/3", "https://tenhou.net/0")
    if not url.startswith("https://tenhou.net/0/?log="):
        raise Exception("Wrong url format, must be a tenhou link with log parameter")

    if url[-5:-1] == "&tw=" and not url[-1].isdigit():
        raise Exception("If 'tw=' is specified, last character must be a digit")

    log_id = url[26:]
    return log_id


def download_one_url_to_xml(url: str, output_dir: str) -> str:
    logging.info("Downloading url %s", url)

    try:
        log_id = get_log_id(url=url)
    except Exception as e:
        logging.error("Cannot extract log id from url: %s", e)
        logging.error("Url format must be 'https://tenhou.net/0/?log=2025010203gm-0029-0000-0123abcd&tw=0'")
        logging.error("Skipping url %s", url)
        raise e

    logging.info("Extracted log id from url: %s", log_id)

    output_file = os.path.join(output_dir, "xml", f"{log_id}.xml")
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        logging.info("Output file %s already exists, don't download", output_file)
        return log_id

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/110.0",
        }
        log_id_without_player = log_id
        if log_id_without_player[-5:-1] == "&tw=" and log_id_without_player[-1].isdigit():
            log_id_without_player = log_id_without_player[:-5]
        download_url = f"https://tenhou.net/0/log/?{log_id_without_player}"
        # JSON logs can be directly downloaded with these two lines:
        # download_url = f"https://tenhou.net/5/mjlog2json.cgi?{log_id_without_player}"
        # headers["Referer"] = f"https://tenhou.net/6/?log={log_id_without_player}"
        # but it doesn't work for custom lobbies
        # so we download XML and then convert to JSON with the 3rd party utility
        response = requests.get(download_url, headers=headers)
        log_content: str = response.text
    except Exception as e:
        logging.error("Cannot download log from tenhou: %s", e)
        raise e

    logging.info("Log content length: %d", len(log_content))
    logging.info("Log content: '%s..........%s'", log_content[:30], log_content[-30:])

    with open(output_file, "w") as f:
        f.write(log_content)
    logging.info("Log content written to file %s", output_file)
    return log_id


def convert_xml_to_json(log_id: str, output_dir: str):
    input_file = os.path.join(output_dir, "xml", f"{log_id}.xml")
    output_file = os.path.join(output_dir, "json", f"{log_id}.json")
    logging.info("Converting xml log %s to json log %s", input_file, output_file)
    result = subprocess.run([
        os.path.abspath(MJLOG2JSON_BINARY_PATH),
        os.path.abspath(input_file),
        "-o", os.path.abspath(output_file),
    ])
    logging.info("Conversion finished with code %d", result.returncode)


def fix_scores_array(scores: list[int], start_score: int):
    assert len(scores) == 4
    logging.info("Scores before: %s", scores)
    for i in range(4):
        scores[i] -= start_score - 25000
    sum_before = sum(scores)
    while True:
        # logging.info("Scores on another iteration: %s", scores)
        # '< 1000' so that everyone can declare riichi
        low_scores = [x for x in scores if x < 1000]
        if len(low_scores) == 0:
            break
        elif len(low_scores) == 1:
            for i in range(4):
                if scores[i] >= 1000:
                    scores[i] -= 100
                else:
                    scores[i] += 300
        elif len(low_scores) == 2:
            for i in range(4):
                if scores[i] >= 1000:
                    scores[i] -= 100
                else:
                    scores[i] += 100
        elif len(low_scores) == 3:
            for i in range(4):
                if scores[i] >= 1000:
                    scores[i] -= 300
                else:
                    scores[i] += 100
    logging.info("Scores after: %s", scores)
    assert sum(scores) == sum_before
    for i in range(4):
        assert scores[i] >= 0
        assert scores[i] % 100 == 0


def fix_scores_in_json_log(log_id: str, output_dir: str, start_score: int):
    log_file = os.path.join(output_dir, "json", f"{log_id}.json")
    with open(log_file, "r") as f:
        json_log = json.load(f)
    logging.info("Loaded json log from file %s", log_file)

    hands = json_log["log"]
    for hand in hands:
        fix_scores_array(scores=hand[1], start_score=start_score)

    with open(log_file, "w") as f:
        json.dump(json_log, f, separators=(",", ":"), ensure_ascii=False)
    logging.info("Scores fixed in json log file %s", log_file)


def main():
    logging.basicConfig(level=0)
    args = parse_args()

    output_dir: str = args.output_dir
    if output_dir is None:
        raise Exception("Must specify --output-dir")

    urls: list[str] = get_url_list(args=args)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "xml"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "json"), exist_ok=True)
    logging.info("Use output dir: %s", output_dir)

    fix_scores: bool = args.fix_scores
    logging.info("Fix scores: %s", fix_scores)

    for url in urls:
        log_id = download_one_url_to_xml(url=url, output_dir=output_dir)
        convert_xml_to_json(log_id=log_id, output_dir=output_dir)
        if fix_scores:
            fix_scores_in_json_log(log_id=log_id, output_dir=output_dir, start_score=30000)
    logging.info("Finished script")


if __name__ == "__main__":
    main()
