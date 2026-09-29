FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy dependency specifications and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Default command points to the FastAPI Mangum handler
# Scheduled worker overrides this with ["worker_handler.handler"]
CMD ["main.handler"]
