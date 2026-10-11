"""Manage v2 acceptance without Blender. Actual observations/user authorization required."""
import argparse
import copy
from pathlib import Path
import sys

from contract import (atomic_write, assert_current, exit_code, init_report, load, record,
                      refresh_status, sync_report, validate_report, waive)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'sync', 'record', 'waive', 'summary'])
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--result', type=Path, help='JSON object or list: id,status,origin,reason,measured,evidence,rule_source')
    parser.add_argument('--check')
    parser.add_argument('--reason')
    parser.add_argument('--confirmation', type=Path, help='JSON {quote,source}; must reference explicit human authorization')
    parser.add_argument('--allow-waived', action='store_true')
    args = parser.parse_args()
    try:
        manifest = load(args.manifest)
        if args.action == 'init':
            if args.report.exists():
                raise ValueError('Report already exists; use sync')
            report = init_report(manifest, args.manifest)
        else:
            report = load(args.report)
            validate_report(report)
            if args.action == 'sync':
                report = sync_report(report, manifest, args.manifest)
            elif args.action == 'record':
                if not args.result:
                    raise ValueError('record requires --result')
                results = load(args.result)
                if isinstance(results, dict):
                    results = [results]
                if not isinstance(results, list) or not results:
                    raise ValueError('Result must be a nonempty object/list')
                staged = copy.deepcopy(report)
                for item in results:
                    allowed = {'id', 'status', 'origin', 'reason', 'measured', 'evidence', 'rule_source'}
                    if not isinstance(item, dict) or set(item) - allowed:
                        raise ValueError('Unknown result fields')
                    record(staged, manifest, args.manifest, item['id'], item['status'], item['origin'],
                           item.get('reason', ''), item.get('measured'), item.get('evidence'), item.get('rule_source'))
                report = staged
            elif args.action == 'waive':
                if not args.check or not args.reason or not args.confirmation:
                    raise ValueError('waive requires --check, --reason, --confirmation')
                waive(report, manifest, args.manifest, args.check, args.reason, load(args.confirmation))
            else:
                assert_current(report, manifest, args.manifest)
        refresh_status(report)
        validate_report(report)
        if args.action != 'summary':
            atomic_write(args.report, report)
        print(report['status'])
        for check in report['checks']:
            if check['required'] and check['status'] not in ('pass', 'not_applicable'):
                print(check['id'], check['status'], check['reason'])
        return exit_code(report['status'], args.allow_waived if args.action == 'summary' else False)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
