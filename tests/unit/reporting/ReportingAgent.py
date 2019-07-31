from pytest import mark

from storyruntime.reporting.ReportingAgent import ReportingAgent


@mark.asyncio
async def test_ensure_interface(magic):
    impl = magic()

    class ReportingAgentSample(ReportingAgent):
        async def capture(self, re):
            impl.received(re)

    sample_agent = ReportingAgentSample()
    re = magic()
    await sample_agent.capture(re)

    impl.received.assert_called_with(re)
