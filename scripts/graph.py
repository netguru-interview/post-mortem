from urllib.request import urlretrieve

from diagrams import Cluster, Diagram
from diagrams.custom import Custom

from diagrams.aws.compute import ECS, AutoScaling, EC2
from diagrams.aws.database import ElastiCache
from diagrams.aws.network import ELB, Route53

kafka_icon = "assets/kafka.png"

with Diagram("Infrastructure architecture", show=False):
    dns = Route53("Smart-Foodies-Shop.com")
    lb = ELB("Load Balancer")

    scaler = AutoScaling("Auto Scaling Group")
    with Cluster("VPC"):
        svc_group = [ECS("Frontend"), EC2("Redis"), EC2("Backend")]

    queue = Custom("Kafka", kafka_icon)
    db = EC2("MySQL")

    dns >> lb >> scaler
    scaler >> svc_group
    svc_group >> db
    svc_group >> queue
