FROM python:3.12-slim

# Install harbor (includes the viewer)
RUN pip install harbor

# Copy jobs data
COPY jobs/ /data/jobs/

EXPOSE 8080

# Run the harbor viewer
CMD ["harbor", "view", "/data/jobs/", "--port", "8080", "--host", "0.0.0.0"]
