import os

import pydantic
import pytest

from app import configurations
from app.adapters import openai
from tests.adapters import mock_data


class Response(pydantic.BaseModel):
    summary: str
    action_items: list[str]


def test_openai_adapter() -> None:
    if os.getenv("RUN_OPENAI_INTEGRATION_TESTS") != "1":
        pytest.skip("Set RUN_OPENAI_INTEGRATION_TESTS=1 to run the live OpenAI adapter test.")

    # Configuration
    env_variables = configurations.EnvConfigs()

    system_prompt = mock_data.SYSTEM_PROMPT
    raw_user_prompt = mock_data.RAW_USER_PROMPT
    transcript = mock_data.TRANSCRIPT

    user_prompt = raw_user_prompt.format(
        transcript=transcript)
    openai_adapter = openai.OpenAIAdapter(env_variables.OPENAI_API_KEY, env_variables.OPENAI_MODEL)

    # action
    response = openai_adapter.run_completion(system_prompt, user_prompt, Response)
    serialized_response = response.model_dump()

    # assert
    print(serialized_response)
    assert "summary" in serialized_response.keys()
    assert "action_items" in serialized_response.keys()
