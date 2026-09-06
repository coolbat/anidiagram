"""Synthetic behavior oracle, independent of AniDiagram's implementation.

The assertions in delivery_truth.json are hand-reviewed facts about this small
program. Passing them does not prove the semantics of arbitrary repositories.
"""


class DeliveryError(Exception):
    pass


class QualityAnalyzer:
    @staticmethod
    def analyze(error_count):
        return {"summary": {"errors": error_count}}


class DeliveryCoordinator:
    @staticmethod
    def deliver(report, render, commit):
        if report["summary"]["errors"] > 0:
            raise DeliveryError("quality gate failed")
        artifact = render()
        receipt = commit(artifact)
        return receipt


def export_direct(renderers, outputs):
    for name, render in renderers:
        outputs[name] = render()


def entry(report, render, commit):
    return DeliveryCoordinator.deliver(report, render, commit)
