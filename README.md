# energy-usage-anomaly-detection-assistant
The energy usage anomaly detection assistant is an LLM based agentic assistant that uses tools to detect anomalies in smart meter data and provide human readable alerts to the customer. 

The customer interacts with the assistant through a streamlit application. The application is deployed to Azure, and can be accessed [here](https://anomalydetectionprodapp.azurewebsites.net/). Please reach out to Robert Mcleod for the password to access the application.

## Local Setup

To run the application locally, follow the steps below:

1. Clone the repository

```bash
git clone https://github.com/robertmcleod2/energy-usage-anomaly-detection-assistant.git
cd energy-usage-anomaly-detection-assistant
```

2. create a virtual environment with python version 3.12. For Conda:

```bash
conda create -n energy-usage-anomaly-detection-assistant python=3.12
conda activate energy-usage-anomaly-detection-assistant
```

3. Install the required packages

```bash
pip install -r requirements_dev.txt
```

4. Set up your local environment variables. Create a `.env` file in the root directory of the project, following the template in the .env_template file. The streamlit password can be set to any value. The `OPENAI_API_KEY` can be obtained from [OpenAI](https://platform.openai.com/api-keys), or reach out to Robert Mcleod for the key.


5. Run the streamlit application

```bash
streamlit run src/app.py
```