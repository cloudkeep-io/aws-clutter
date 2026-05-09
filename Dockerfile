FROM public.ecr.aws/lambda/python:3.8

COPY app.py ${LAMBDA_TASK_ROOT}

ARG PKG_VER
COPY dist/detached_ebs_cost_monitor-${PKG_VER}-py3-none-any.whl .
RUN pip3 install detached_ebs_cost_monitor-${PKG_VER}-py3-none-any.whl --target "${LAMBDA_TASK_ROOT}"

CMD [ "app.handler" ]
