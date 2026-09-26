ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python and required packages
RUN apk add --no-cache python3 py3-pip py3-requests

# Copy the bridge script
COPY run.sh /
COPY cartrack2traccar.py /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
