Running
=======

Locally via Docker
------------------

To pull the Docker image

.. code-block:: bash

    docker pull jantman/ecsjobs:latest

To run locally via Docker to validate a configuration directory ``./conf``:

.. code-block:: bash

    docker run -it --rm \
      -e ECSJOBS_LOCAL_CONF_PATH=/tmp/conf \
      -v $(pwd)/conf:/tmp/conf \
      jantman/ecsjobs:latest \
      validate

To run the "foo" schedule locally in a detached/background container (i.e. as a cron job) and allow it to run Docker execs, assuming your Docker socket is at ``/var/run/docker.sock``, your configuration directory is at ``./conf``, and you want to use AWS credentials from ``~/.aws/credentials``:

.. code-block:: bash

    docker run --rm -d \
      -e ECSJOBS_LOCAL_CONF_PATH=/tmp/conf \
      -e DOCKER_HOST=unix:///tmp/docker.sock \
      -v $(pwd)/conf:/tmp/conf \
      -v /var/run/docker.sock:/tmp/docker.sock \
      -v $(readlink -f ~/.aws/credentials):/root/.aws/credentials \
      jantman/ecsjobs:latest \
      run foo

Note that when running in this method, the ``LocalCommand`` class runs commands inside the ecsjobs Docker container, not on the host system.

Locally via pip
---------------

To run locally directly on the host OS, i.e. so the ``LocalCommand`` class will run commands on the host, first setup a virtualenv and install ecsjobs:

.. code-block:: bash

    virtualenv --python=python3.6 .
    source bin/activate
    pip install ecsjobs

To run the "foo" schedule locally using a configuration directory at ``./conf``:

.. code-block:: bash

    ECSJOBS_LOCAL_CONF_PATH=$(readlink -f ./conf) ecsjobs run foo

In ECS
------

Note that because of how ECS Scheduled Tasks work, you'll need to create a separate Task Definition for
each schedule that you want ecsjobs to run. As an example, if your jobs have two different ``schedule``
values, "daily" and "weekly", you'd need to create two separate ECS Task Definitions that differ only
by the command they run (``run daily`` and ``run weekly``, respectively).

To run ecsjobs as an ECS Scheduled Task, you'll need to create an ECS Task Definition for the task and an IAM Role to run the task with. You'll also need to create a CloudWatch Event Rule, CloudWatch Event Target, and IAM Role for CloudWatch to trigger the Task, but these are easily done either through the AWS Console or various automation tools.

The IAM Policy that I use on my ecsjobs role is below; it also includes a "AllowSnapshotManagement" statement to allow management of EBS Snapshots, because I do this via a command executed directly in the ecsjobs container.

.. code-block:: json

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "AllowDescribeSSMParams",
          "Action": ["ssm:DescribeParameters"],
          "Effect": "Allow",
          "Resource": "*"
        },
        {
          "Sid": "AllowGetSSMParams",
          "Action": ["ssm:GetParameters"],
          "Effect": "Allow",
          "Resource": "arn:aws:ssm:$${aws_region}:$${account_id}:parameter/*"
        },
        {
          "Sid": "AllowS3",
          "Action": ["s3:Get*", "s3:List*", "s3:Head*"],
          "Effect": "Allow",
          "Resource": "*"
        },
        {
          "Sid": "AllowCloudwatch",
          "Action": ["cloudwatch:List*", "cloudwatch:PutMetricData"],
          "Effect": "Allow",
          "Resource": "*"
        },
        {
          "Sid": "AllowECS",
          "Action": ["ecs:RunTask", "ecs:Describe*", "ecs:List*", "ecs:Discover*"],
          "Effect": "Allow",
          "Resource": "*"
        },
        {
          "Sid": "AllowCWLogs",
          "Action": ["logs:FilterLogEvents", "logs:Describe*", "logs:Get*"],
          "Effect": "Allow",
          "Resource": "*"
        },
        {
          "Sid": "AllowSesSend",
          "Action": ["ses:SendEmail"],
          "Effect": "Allow",
          "Resource": "*"
        },
        {
          "Sid": "AllowSnapshotManagement",
          "Action": ["ec2:CreateSnapshot", "ec2:DeleteSnapshot", "ec2:Describe*", "ec2:CreateTags", "ec2:ModifySnapshotAttribute", "ec2:ResetSnapshotAttribute"],
          "Effect": "Allow",
          "Resource": "*"
        }
      ]
    }

The container definition that I use in my Task Definition for ecsjobs is as follows:

.. code-block:: json

    [
      {
        "name": "ecsjobs",
        "image": "jantman/ecsjobs:latest",
        "command": ["run", "${var.schedule}"],
        "cpu": 64,
        "memoryReservation": 64,
        "environment": [
          {"name": "DOCKER_HOST", "value": "unix:///tmp/docker.sock"},
          {"name": "ECSJOBS_BUCKET", "value": "${var.bucket_name}"},
          {"name": "ECSJOBS_KEY", "value": "${var.bucket_key}"},
          {"name": "AWS_REGION", "value": "us-west-2"},
          {"name": "AWS_DEFAULT_REGION", "value": "us-west-2"}
        ],
        "essential": true,
        "mountPoints": [
          {
            "sourceVolume": "dockersock",
            "containerPath": "/tmp/docker.sock"
          }
        ],
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
            "awslogs-region": "us-west-2",
            "awslogs-group": "${var.log_group_name}",
            "awslogs-stream-prefix": "${var.cluster_name}"
          }
        }
      }
    ]

This is actually a snippet from a terraform configuration. A few notes about it:

* The "command" in the container definition references a ``${var.schedule}`` variable that defines the schedule name. I have two task definitions, one for my daily schedule and one for my weekly schedule.
* In order to be able to run Docker Execs on the ECS host, i.e. against another ECS container, we mount ``/var/run/docker.sock`` from the host into the container at ``/tmp/docker.sock``. The ``DOCKER_HOST`` environment variable must be set to the path of the socket (prefixed with ``unix://`` to denote that it's a socket).
* The ``ECSJOBS_BUCKET`` and ``ECSJOBS_KEY`` environment variables specify the bucket name and key (in that bucket) to retrieve configuration from.
* The ``${var.log_group_name}`` and ``${var.cluster_name}`` variables specify settings for the ``awslogs`` Docker logging driver, to send container logs to CloudWatch Logs.

Suppressing Reports for Successful Runs
---------------------------------------

If you do not wish to send an email report if all jobs ran successfully, you can pass the ``-m`` / ``--only-email-if-problems`` command line argument to ecsjobs.
