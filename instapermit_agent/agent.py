import os

import dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

dotenv.load_dotenv()

KEY_OPENROUTER = 'OPENROUTER_API_KEY_RPA_AGENT'
if KEY_OPENROUTER not in os.environ:
    raise KeyError(f'Environment variable `{KEY_OPENROUTER}` not found. Add the API key to the `.env` file.')

KEY_USERNAME = 'AHJ_CREDENTIAL_USERNAME'
KEY_PASSWORD = 'AHJ_CREDENTIAL_PASSWORD'


def get_login_credentials(login_url: str) -> dict:
    """
    Retrieve the login credentials (username and password) for a given AHJ website.
    :param login_url: URL of the login page.
    :return: A dictionary with a 'status' flag, either 'success' or 'error'.
        If 'success', then credentials are provided with keys 'username' and 'password'.
        If 'error', then 'error_message' is provided.
    """
    # TODO: Retrieve via async/await network call.
    if KEY_USERNAME in os.environ and KEY_PASSWORD in os.environ:
        return {
            'status': 'success',
            'username': os.environ[KEY_USERNAME],
            'password': os.environ[KEY_PASSWORD]
        }
    return {
        'status': 'error',
        'error_message': 'Credentials were not found amongst environment variables.'
    }

ROOT_STATIC_INSTRUCTION = """
# Permit Submittal

Our overall goal is to submit a light construction permit within a given AHJ
(Authority Having Jurisdiction), such as a city or county.
We are using Playwright to navigate through a browser window, fill out the
online form, and submit any relevant documents.
We will have to read any error messages that appear on screen and do our best
to remediate those errors.

## Rules

- Use a Chrome browser by default.
- Values for form fields are provided in the file `payload.json`.
"""

root_agent = LlmAgent(
    name='root_agent',
    description='An agent to submit and retrieve solar permits within websites for various AHJs.',
    model=LiteLlm(
        model='openrouter/moonshotai/kimi-k2.5',
        api_key=os.environ[KEY_OPENROUTER],
        api_base='https://openrouter.ai/api/v1'
    ),
    instruction='Walk through a permit submittal.',
    static_instruction=ROOT_STATIC_INSTRUCTION,
    tools=[
        get_login_credentials,
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='npx',
                    # `0.0.56` because of JSON schema version 2020-12:
                    # https://github.com/microsoft/playwright-mcp/issues/1357
                    args=['-y', '@playwright/mcp@0.0.56']
                ),
                timeout=15  # Maximum seconds the agent may wait before a timeout error occurs.
            ),
            tool_filter=[
                'browser_click',
                'browser_close',
                'browser_console_messages',
                'browser_drag',
                'browser_evaluate',
                'browser_file_upload',
                'browser_fill_form',
                'browser_handle_dialog',
                'browser_hover',
                'browser_navigate',
                'browser_navigate_back',
                'browser_network_requests',
                'browser_press_key',
                'browser_resize',
                # 'browser_run_code',  # Agent tends to fall back to this often; it rarely helps.
                'browser_select_option',
                'browser_snapshot',
                'browser_take_screenshot',
                'browser_type',
                'browser_wait_for'
            ],
            require_confirmation=False
        )
    ]
)
