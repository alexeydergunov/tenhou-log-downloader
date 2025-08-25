#!./venv/bin/python3

import logging
import os
from argparse import ArgumentParser
from typing import Optional

import requests


def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-i", "--input-file")
    arg_parser.add_argument("-u", "--url")
    arg_parser.add_argument("-o", "--output-dir")
    arg_parser.add_argument("-t", "--type", choices=["xml", "json"])
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

    if url[-5:-1] == "&tw=" and url[-1].isdigit():
        url = url[:-5]

    log_id = url[26:]
    return log_id


def download_one_url(url: str, output_dir: str, log_type: str):
    logging.info("Downloading url %s", url)

    try:
        log_id = get_log_id(url=url)
    except Exception as e:
        logging.error("Cannot extract log id from url: %s", e)
        logging.error("Url format must be 'https://tenhou.net/0/?log=2025010203gm-0029-0000-0123abcd&tw=0'")
        logging.error("Skipping url %s", url)
        return

    logging.info("Extracted log id from url: %s", log_id)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/110.0",
        }
        if log_type == "json":
            download_url = f"https://tenhou.net/5/mjlog2json.cgi?{log_id}"
            headers["Referer"] = f"https://tenhou.net/6/?log={log_id}"
        else:
            download_url = f"https://tenhou.net/0/log/?{log_id}"
        response = requests.get(download_url, headers=headers)
        log_content: str = response.text
    except Exception as e:
        logging.error("Cannot download log from tenhou: %s", e)
        return

    logging.info("Log content length: %d", len(log_content))
    logging.info("Log content: '%s..........%s'", log_content[:30], log_content[-30:])

    output_file = os.path.join(output_dir, log_type, f"{log_id}.{log_type}")
    with open(output_file, "w") as f:
        f.write(log_content)
    logging.info("Log content written to file %s", output_file)


def main():
    logging.basicConfig(level=0)
    args = parse_args()

    output_dir: str = args.output_dir
    if output_dir is None:
        raise Exception("Must specify --output-dir")

    urls: list[str] = get_url_list(args=args)

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    logging.info("Use output dir: %s", output_dir)

    log_type: str = args.type
    logging.info("Log type: %s", log_type)
    output_dir_with_type = os.path.join(output_dir, log_type)
    if not os.path.exists(output_dir_with_type):
        os.mkdir(output_dir_with_type)

    for url in urls:
        download_one_url(url=url, output_dir=output_dir, log_type=log_type)
    logging.info("Finished script")


if __name__ == "__main__":
    main()
