import argparse
import logging

from oci import config
from oci import gerrit
from oci import jenkins


def main():
    parser = argparse.ArgumentParser(
        description='A command line tool for working with Ovirt CI')

    parser.add_argument(
        '--verbose',
        help="increase output verbosity",
        action="store_true")
    subparsers = parser.add_subparsers(title="commands")

    build_artifacts = subparsers.add_parser(
        "build-artifacts",
        help="start the build-artifacts stage")
    build_artifacts.set_defaults(command=run_build_artifacts)

    build_artifacts.add_argument(
        'change',
        help='number of the patch to run')

    args = parser.parse_args()
    args.command(args)


def run_build_artifacts(args):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s")

    log = logging.getLogger("build-artifacts")
    if not args.verbose:
        logging.disable(logging.CRITICAL)

    cfg = config.load()

    ga = gerrit.API(host=cfg.gerrit.host)

    ja = jenkins.API(
        host=cfg.jenkins.host,
        user_id=cfg.jenkins.user_id,
        api_token=cfg.jenkins.api_token)

    log.info("[ 1/5 ] Getting build info for change %s", args.change)
    info = ga.build_info(args.change)

    log.info("[ 2/5 ] Starting build-artifacts job for %s", info)
    queue_url = ja.run(
        url=info["url"], ref=info["ref"], stage="build-artifacts")

    log.info("[ 3/5 ] Waiting for queue item %s", queue_url)
    job_url = ja.wait_for_queue(queue_url)

    log.info("[ 4/5 ] Waiting for job %s", job_url)
    result = ja.wait_for_job(job_url)

    log.info("[ 5/5 ] Job completed with %s", result)


if __name__ == "__main__":
    main()
