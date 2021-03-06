Introduction
============

On September 21st, 2020, we have experienced a major service outage for
our company's corporate website - Smart-Foodies-Shop.com. The outage was
caused by an accidental removal of system data from our database server.
This incident caused the service to be unavailable for a couple of
hours. We also lost some production data that we were eventually unable
to recover.

Background
==========

Smart-Foodies-Shop.com used a single MySQL database instance running on
EC2 as a production database server. For security reasons there was a
business decision made to host a database on a single, separate compute
instance. It's installed natively on the host and backed exclusively by
instance storage. In this setup a single database has to handle all the
load, which is not ideal.

Related architecture is depicted below.

[![](assets/infrastructure_architecture.png)](assets/infrastructure_architecture.png)

Timeline
========

On September 21st, 2020 an engineer started onboarding process onto RDS,
to which our company is planning to migrate. The plan was to try out new
managed solution and compare it with existing one to see if we could
benefit from better performance and minimize load on our database.

± 16:00 UTC: prior to starting this work, our engineer decided to dump
the production database using custom shell script. This was required to
ensure the new RDS instance would be up to date. Daily dumps however
normally happen automatically once every 24 hours and are later uploaded
to S3, but this time it was necessary to have a more up to date copy of
the database.

± 17:00 UTC: Smart-Foodies-Shop.com starts experiencing an increase in
database load due to what we suspect was an overly complicated SQL
export query consisting of multiple `JOIN` sub-queries resulting in huge
temporary table being generated. One of the problems this load caused
was that many customers were not able to finish their purchases on our
website. Getting the load under control took several hours.

± 17:20 UTC: one of the engineers thinks that perhaps export script had
created some files in the MySQL data directory during the previous
attempts to run it. While normally dump script just exports entire
database without altering its content, this time engineer decided to
slightly modify its logic and extract only product-specific data, hence
trying to remove various client-related tables and purchase histories.
This resulted in an utterly large disk consumption being occupied by
`/var/lib/mysql` directory in at attempt of MySQL Engine to process
`JOIN` query, which later had filled in entire disk space to its maximum
extent.

Trying to restore the space consumption, an engineer proceeds to wipe
the `/var/lib/mysql` directory, thinking this is `/var/log/mysql`. A
second after, understanding what is happening, the engineer terminated
the process but at this point around 50 GB of data had already been
removed.

Recovery Procedures
==========================

In our case we have the following procedures in place:

Every 24 hours we generate a backup of production database. This backup
is then uploaded into S3, allowing us to restore a database in
relatively little time.

At the time of the outage we had one backup available: a backup created
almost 24 hours before the situation happened.

Recovering Smart-Foodies-Shop.com
=================================

To recover we decided to use the aforementioned backup created 24 hours
before the outage, as it was our only option. The restoration process
included:

-   spin up a new EC2 instance using the same AMI as production database
    server
-   rsync missing `/var/lib` parts that had accidentally been deleted
-   copy over the existing latest backup from S3 onto production and
    restore database from it
-   gradually re-enable existing web services

On September 22nd at 02:00 UTC we managed to restore the
Smart-Foodies-Shop.com server and database.

Data Loss Impact
================

Database data such as users, comments and orders created between
September 21st 16:20 UTC and Sepm 22nd 02:30 UTC has been lost. It's
hard to estimate how much data has been lost exactly, but we estimate we
have lost at least 100 new users, 500 comments, and roughly 1000 orders.

Root Cause Analysis
===================

-   **Why was Smart-Foodies-Shop.com down?** - The database directory of
    the database server was removed by accident, instead of removing the
    temporary generated cache.
-   **Why was the database directory removed?** - Database was going to
    be migrated to RDS managed instance, this required testing with the
    latest database snapshot. This, in turn required that the dump
    script had to be updated and manually executed on a production
    database server.
-   **Why did script had to be updated?** - To get rid of client's
    private data, so engineer could test data in a new staging
    environment.
-   **Why did the database load increase?** - This was caused by an
    over-convoluted `JOIN` query to export latest database snapshot.

Next Steps
==========

Backup Enhancements
-------------------

Backup procedures should definitely be enhanced. One way to accomplish
better recovery is by leveraging LVM volumes and EBS. This might provide
the option to easily increase the size of the volumes by adding more EBS
volumes. With multiple EBS volumes, network performance is increased
between EC2 instances and EBS volumes and also allows you to restore
specific part of your partitions without fetching remote backups. EBS
however can be really slow if not using an S-Tier offering, hence the
disks can be very slow, resulting in them being the main bottleneck in
the restoration process.

Migrating to RDS
-------------------

Even though migration to managed RDS service had ironically been a semi
root cause for entire hick-up, we are still going to switch to a more
sophisticated solution and from now on will treat our production as a
higher class citizen and will try to leverage advanced high availability
setups to prevent future outages and stay fault tolerant even when one
of our worker nodes goes down.
