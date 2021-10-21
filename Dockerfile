FROM public.ecr.aws/lambda/python:3.8

COPY app.py ${LAMBDA_TASK_ROOT}

ARG PKG_VER
COPY dist/aws_clutter_meter-${PKG_VER}-py3-none-any.whl .
RUN pip3 install aws_clutter_meter-${PKG_VER}-py3-none-any.whl --target "${LAMBDA_TASK_ROOT}"

CMD [ "app.handler" ]
