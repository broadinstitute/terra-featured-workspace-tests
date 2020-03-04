FROM broadinstitute/firecloud-tools:dev

RUN pip3 install tenacity
RUN pip3 install --upgrade firecloud
# RUN pip3 install --upgrade google-cloud-storage