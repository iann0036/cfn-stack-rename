import boto3
import sys
import json
import time
import pprint
from collections import OrderedDict
from cfn_flip import flip, to_yaml, to_json

resolve_matches = {}

def resolvePropertyValue(prop, match_resources, replace_values):
    if isinstance(prop, dict):
        if 'Ref' in prop:
            if prop['Ref'] in match_resources:
                if replace_values:
                    return resolve_matches['Ref' + prop['Ref']]
                else:
                    resolve_matches['Ref' + prop['Ref']] = {
                        'Ref': prop['Ref']
                    }
        elif 'Fn::GetAtt' in prop:
            if prop['Fn::GetAtt'][0] in match_resources:
                if replace_values:
                    return resolve_matches['GetAtt' + prop['Fn::GetAtt'][0] + prop['Fn::GetAtt'][1]]
                else:
                    resolve_matches['GetAtt' + prop['Fn::GetAtt'][0] + prop['Fn::GetAtt'][1]] = {
                        'Fn::GetAtt': prop['Fn::GetAtt']
                    }
        elif 'Fn::Sub' in prop:
            pass # TODO
        
        ret = {}
        for k, v in prop.items():
            ret[k] = resolvePropertyValue(v, match_resources, replace_values)
        return ret
    elif isinstance(prop, list) and not isinstance(prop, str):
        ret = []
        for listitem in prop:
            ret.append(resolvePropertyValue(listitem, match_resources, replace_values))
        return ret
    else:
        return prop

eligible_import_resources = { # from Former2
    "AWS::ACMPCA::Certificate": {
        "importProperties": [
            "Arn",
            "CertificateAuthorityArn"
        ]
    },
    "AWS::ACMPCA::CertificateAuthority": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ACMPCA::CertificateAuthorityActivation": {
        "importProperties": [
            "CertificateAuthorityArn"
        ]
    },
    "AWS::AccessAnalyzer::Analyzer": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ApiGateway::Authorizer": {
        "importProperties": [
            "RestApiId",
            "AuthorizerId"
        ]
    },
    "AWS::ApiGateway::ClientCertificate": {
        "importProperties": [
            "ClientCertificateId"
        ]
    },
    "AWS::ApiGateway::Deployment": {
        "importProperties": [
            "RestApiId",
            "DeploymentId"
        ]
    },
    "AWS::ApiGateway::DocumentationVersion": {
        "importProperties": [
            "DocumentationVersion",
            "RestApiId"
        ]
    },
    "AWS::ApiGateway::DomainName": {
        "importProperties": [
            "DomainName"
        ]
    },
    "AWS::ApiGateway::Method": {
        "importProperties": [
            "RestApiId",
            "ResourceId",
            "HttpMethod"
        ]
    },
    "AWS::ApiGateway::Model": {
        "importProperties": [
            "RestApiId",
            "Name"
        ]
    },
    "AWS::ApiGateway::RequestValidator": {
        "importProperties": [
            "RestApiId",
            "RequestValidatorId"
        ]
    },
    "AWS::ApiGateway::Resource": {
        "importProperties": [
            "RestApiId",
            "ResourceId"
        ]
    },
    "AWS::ApiGateway::RestApi": {
        "importProperties": [
            "RestApiId"
        ]
    },
    "AWS::ApiGateway::Stage": {
        "importProperties": [
            "RestApiId",
            "StageName"
        ]
    },
    "AWS::AppFlow::ConnectorProfile": {
        "importProperties": [
            "ConnectorProfileName"
        ]
    },
    "AWS::AppFlow::Flow": {
        "importProperties": [
            "FlowName"
        ]
    },
    "AWS::ApplicationInsights::Application": {
        "importProperties": [
            "ApplicationARN"
        ]
    },
    "AWS::Athena::DataCatalog": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::Athena::NamedQuery": {
        "importProperties": [
            "NamedQueryId"
        ]
    },
    "AWS::Athena::WorkGroup": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::AuditManager::Assessment": {
        "importProperties": [
            "AssessmentId"
        ]
    },
    "AWS::AutoScaling::AutoScalingGroup": {
        "importProperties": [
            "AutoScalingGroupName"
        ]
    },
    "AWS::AutoScaling::LaunchConfiguration": {
        "importProperties": [
            "LaunchConfigurationName"
        ]
    },
    "AWS::AutoScaling::LifecycleHook": {
        "importProperties": [
            "AutoScalingGroupName",
            "LifecycleHookName"
        ]
    },
    "AWS::AutoScaling::ScalingPolicy": {
        "importProperties": [
            "PolicyName"
        ]
    },
    "AWS::AutoScaling::ScheduledAction": {
        "importProperties": [
            "ScheduledActionName"
        ]
    },
    "AWS::CE::CostCategory": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::Cassandra::Keyspace": {
        "importProperties": [
            "KeyspaceName"
        ]
    },
    "AWS::Cassandra::Table": {
        "importProperties": [
            "KeyspaceName",
            "TableName"
        ]
    },
    "AWS::Chatbot::SlackChannelConfiguration": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::CloudFormation::ModuleDefaultVersion": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::CloudFormation::ModuleVersion": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::CloudFormation::Stack": {
        "importProperties": [
            "StackId"
        ]
    },
    "AWS::CloudFormation::StackSet": {
        "importProperties": [
            "StackSetId"
        ]
    },
    "AWS::CloudFront::CachePolicy": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::CloudFront::KeyGroup": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::CloudFront::OriginRequestPolicy": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::CloudFront::PublicKey": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::CloudFront::RealtimeLogConfig": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::CloudTrail::Trail": {
        "importProperties": [
            "TrailName"
        ]
    },
    "AWS::CloudWatch::Alarm": {
        "importProperties": [
            "AlarmName"
        ]
    },
    "AWS::CloudWatch::CompositeAlarm": {
        "importProperties": [
            "AlarmName"
        ]
    },
    "AWS::CloudWatch::MetricStream": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::CodeArtifact::Domain": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::CodeArtifact::Repository": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::CodeGuruProfiler::ProfilingGroup": {
        "importProperties": [
            "ProfilingGroupName"
        ]
    },
    "AWS::CodeGuruReviewer::RepositoryAssociation": {
        "importProperties": [
            "AssociationArn"
        ]
    },
    "AWS::CodeStarConnections::Connection": {
        "importProperties": [
            "ConnectionArn"
        ]
    },
    "AWS::Config::ConformancePack": {
        "importProperties": [
            "ConformancePackName"
        ]
    },
    "AWS::Config::OrganizationConformancePack": {
        "importProperties": [
            "OrganizationConformancePackName"
        ]
    },
    "AWS::Config::StoredQuery": {
        "importProperties": [
            "QueryName"
        ]
    },
    "AWS::DataBrew::Dataset": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::DataBrew::Job": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::DataBrew::Project": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::DataBrew::Recipe": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::DataBrew::Schedule": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::DataSync::Agent": {
        "importProperties": [
            "AgentArn"
        ]
    },
    "AWS::DataSync::LocationEFS": {
        "importProperties": [
            "LocationArn"
        ]
    },
    "AWS::DataSync::LocationFSxWindows": {
        "importProperties": [
            "LocationArn"
        ]
    },
    "AWS::DataSync::LocationNFS": {
        "importProperties": [
            "LocationArn"
        ]
    },
    "AWS::DataSync::LocationObjectStorage": {
        "importProperties": [
            "LocationArn"
        ]
    },
    "AWS::DataSync::LocationS3": {
        "importProperties": [
            "LocationArn"
        ]
    },
    "AWS::DataSync::LocationSMB": {
        "importProperties": [
            "LocationArn"
        ]
    },
    "AWS::DataSync::Task": {
        "importProperties": [
            "TaskArn"
        ]
    },
    "AWS::Detective::Graph": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::Detective::MemberInvitation": {
        "importProperties": [
            "GraphArn",
            "MemberId"
        ]
    },
    "AWS::DevOpsGuru::NotificationChannel": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::DevOpsGuru::ResourceCollection": {
        "importProperties": [
            "ResourceCollectionType"
        ]
    },
    "AWS::DynamoDB::Table": {
        "importProperties": [
            "TableName"
        ]
    },
    "AWS::EC2::CarrierGateway": {
        "importProperties": [
            "CarrierGatewayId"
        ]
    },
    "AWS::EC2::EIP": {
        "importProperties": [
            "PublicIp"
        ]
    },
    "AWS::EC2::FlowLog": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::EC2::GatewayRouteTableAssociation": {
        "importProperties": [
            "GatewayId"
        ]
    },
    "AWS::EC2::Instance": {
        "importProperties": [
            "InstanceId"
        ]
    },
    "AWS::EC2::InternetGateway": {
        "importProperties": [
            "InternetGatewayId"
        ]
    },
    "AWS::EC2::LocalGatewayRoute": {
        "importProperties": [
            "DestinationCidrBlock",
            "LocalGatewayRouteTableId"
        ]
    },
    "AWS::EC2::LocalGatewayRouteTableVPCAssociation": {
        "importProperties": [
            "LocalGatewayRouteTableVpcAssociationId"
        ]
    },
    "AWS::EC2::NatGateway": {
        "importProperties": [
            "NatGatewayId"
        ]
    },
    "AWS::EC2::NetworkAcl": {
        "importProperties": [
            "NetworkAclId"
        ]
    },
    "AWS::EC2::NetworkInsightsAnalysis": {
        "importProperties": [
            "NetworkInsightsAnalysisId"
        ]
    },
    "AWS::EC2::NetworkInsightsPath": {
        "importProperties": [
            "NetworkInsightsPathId"
        ]
    },
    "AWS::EC2::NetworkInterface": {
        "importProperties": [
            "NetworkInterfaceId"
        ]
    },
    "AWS::EC2::PrefixList": {
        "importProperties": [
            "PrefixListId"
        ]
    },
    "AWS::EC2::RouteTable": {
        "importProperties": [
            "RouteTableId"
        ]
    },
    "AWS::EC2::SecurityGroup": {
        "importProperties": [
            "GroupId"
        ]
    },
    "AWS::EC2::Subnet": {
        "importProperties": [
            "SubnetId"
        ]
    },
    "AWS::EC2::VPC": {
        "importProperties": [
            "VpcId"
        ]
    },
    "AWS::EC2::Volume": {
        "importProperties": [
            "VolumeId"
        ]
    },
    "AWS::ECR::PublicRepository": {
        "importProperties": [
            "RepositoryName"
        ]
    },
    "AWS::ECR::Repository": {
        "importProperties": [
            "RepositoryName"
        ]
    },
    "AWS::ECS::CapacityProvider": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::ECS::Cluster": {
        "importProperties": [
            "ClusterName"
        ]
    },
    "AWS::ECS::PrimaryTaskSet": {
        "importProperties": [
            "Cluster",
            "Service"
        ]
    },
    "AWS::ECS::Service": {
        "importProperties": [
            "ServiceArn",
            "Cluster"
        ]
    },
    "AWS::ECS::TaskDefinition": {
        "importProperties": [
            "TaskDefinitionArn"
        ]
    },
    "AWS::ECS::TaskSet": {
        "importProperties": [
            "Cluster",
            "Service",
            "Id"
        ]
    },
    "AWS::EFS::AccessPoint": {
        "importProperties": [
            "AccessPointId"
        ]
    },
    "AWS::EFS::FileSystem": {
        "importProperties": [
            "FileSystemId"
        ]
    },
    "AWS::EKS::FargateProfile": {
        "importProperties": [
            "ClusterName",
            "FargateProfileName"
        ]
    },
    "AWS::ElastiCache::User": {
        "importProperties": [
            "UserId"
        ]
    },
    "AWS::ElastiCache::UserGroup": {
        "importProperties": [
            "UserGroupId"
        ]
    },
    "AWS::ElasticLoadBalancing::LoadBalancer": {
        "importProperties": [
            "LoadBalancerName"
        ]
    },
    "AWS::ElasticLoadBalancingV2::Listener": {
        "importProperties": [
            "ListenerArn"
        ]
    },
    "AWS::ElasticLoadBalancingV2::ListenerRule": {
        "importProperties": [
            "RuleArn"
        ]
    },
    "AWS::ElasticLoadBalancingV2::LoadBalancer": {
        "importProperties": [
            "LoadBalancerArn"
        ]
    },
    "AWS::EventSchemas::RegistryPolicy": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Events::Archive": {
        "importProperties": [
            "ArchiveName"
        ]
    },
    "AWS::Events::Rule": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::FMS::NotificationChannel": {
        "importProperties": [
            "SnsTopicArn"
        ]
    },
    "AWS::FMS::Policy": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::GameLift::Alias": {
        "importProperties": [
            "AliasId"
        ]
    },
    "AWS::GameLift::GameServerGroup": {
        "importProperties": [
            "GameServerGroupArn"
        ]
    },
    "AWS::GlobalAccelerator::Accelerator": {
        "importProperties": [
            "AcceleratorArn"
        ]
    },
    "AWS::GlobalAccelerator::EndpointGroup": {
        "importProperties": [
            "EndpointGroupArn"
        ]
    },
    "AWS::GlobalAccelerator::Listener": {
        "importProperties": [
            "ListenerArn"
        ]
    },
    "AWS::Glue::Registry": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::Glue::Schema": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::Glue::SchemaVersion": {
        "importProperties": [
            "VersionId"
        ]
    },
    "AWS::Glue::SchemaVersionMetadata": {
        "importProperties": [
            "SchemaVersionId",
            "Key",
            "Value"
        ]
    },
    "AWS::GreengrassV2::ComponentVersion": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::IVS::Channel": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::IVS::PlaybackKeyPair": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::IVS::StreamKey": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ImageBuilder::Component": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ImageBuilder::DistributionConfiguration": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ImageBuilder::Image": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ImageBuilder::ImagePipeline": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ImageBuilder::ImageRecipe": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::ImageBuilder::InfrastructureConfiguration": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::IoT::Authorizer": {
        "importProperties": [
            "AuthorizerName"
        ]
    },
    "AWS::IoT::Certificate": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::IoT::DomainConfiguration": {
        "importProperties": [
            "DomainConfigurationName"
        ]
    },
    "AWS::IoT::ProvisioningTemplate": {
        "importProperties": [
            "TemplateName"
        ]
    },
    "AWS::IoT::Thing": {
        "importProperties": [
            "ThingName"
        ]
    },
    "AWS::IoT::TopicRuleDestination": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::IoTSiteWise::AccessPolicy": {
        "importProperties": [
            "AccessPolicyId"
        ]
    },
    "AWS::IoTSiteWise::Asset": {
        "importProperties": [
            "AssetId"
        ]
    },
    "AWS::IoTSiteWise::AssetModel": {
        "importProperties": [
            "AssetModelId"
        ]
    },
    "AWS::IoTSiteWise::Dashboard": {
        "importProperties": [
            "DashboardId"
        ]
    },
    "AWS::IoTSiteWise::Gateway": {
        "importProperties": [
            "GatewayId"
        ]
    },
    "AWS::IoTSiteWise::Portal": {
        "importProperties": [
            "PortalId"
        ]
    },
    "AWS::IoTSiteWise::Project": {
        "importProperties": [
            "ProjectId"
        ]
    },
    "AWS::IoTWireless::Destination": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::IoTWireless::DeviceProfile": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::IoTWireless::ServiceProfile": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::IoTWireless::WirelessDevice": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::IoTWireless::WirelessGateway": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::KMS::Alias": {
        "importProperties": [
            "AliasName"
        ]
    },
    "AWS::KMS::Key": {
        "importProperties": [
            "KeyId"
        ]
    },
    "AWS::Kendra::DataSource": {
        "importProperties": [
            "Id",
            "IndexId"
        ]
    },
    "AWS::Kendra::Faq": {
        "importProperties": [
            "Id",
            "IndexId"
        ]
    },
    "AWS::Kendra::Index": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Kinesis::Stream": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::KinesisFirehose::DeliveryStream": {
        "importProperties": [
            "DeliveryStreamName"
        ]
    },
    "AWS::Lambda::Alias": {
        "importProperties": [
            "AliasArn"
        ]
    },
    "AWS::Lambda::CodeSigningConfig": {
        "importProperties": [
            "CodeSigningConfigArn"
        ]
    },
    "AWS::Lambda::EventSourceMapping": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Lambda::Function": {
        "importProperties": [
            "FunctionName"
        ]
    },
    "AWS::Lambda::Version": {
        "importProperties": [
            "FunctionArn"
        ]
    },
    "AWS::LicenseManager::Grant": {
        "importProperties": [
            "GrantArn"
        ]
    },
    "AWS::LicenseManager::License": {
        "importProperties": [
            "LicenseArn"
        ]
    },
    "AWS::Logs::LogGroup": {
        "importProperties": [
            "LogGroupName"
        ]
    },
    "AWS::Logs::MetricFilter": {
        "importProperties": [
            "FilterName"
        ]
    },
    "AWS::Logs::SubscriptionFilter": {
        "importProperties": [
            "LogGroupName",
            "FilterName"
        ]
    },
    "AWS::MWAA::Environment": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::Macie::CustomDataIdentifier": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Macie::FindingsFilter": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Macie::Session": {
        "importProperties": [
            "AwsAccountId"
        ]
    },
    "AWS::MediaConnect::Flow": {
        "importProperties": [
            "FlowArn"
        ]
    },
    "AWS::MediaConnect::FlowEntitlement": {
        "importProperties": [
            "EntitlementArn"
        ]
    },
    "AWS::MediaConnect::FlowOutput": {
        "importProperties": [
            "OutputArn"
        ]
    },
    "AWS::MediaConnect::FlowSource": {
        "importProperties": [
            "SourceArn"
        ]
    },
    "AWS::MediaConnect::FlowVpcInterface": {
        "importProperties": [
            "FlowArn",
            "Name"
        ]
    },
    "AWS::MediaPackage::Asset": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::MediaPackage::Channel": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::MediaPackage::OriginEndpoint": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::MediaPackage::PackagingConfiguration": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::MediaPackage::PackagingGroup": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::NetworkFirewall::Firewall": {
        "importProperties": [
            "FirewallArn"
        ]
    },
    "AWS::NetworkFirewall::FirewallPolicy": {
        "importProperties": [
            "FirewallPolicyArn"
        ]
    },
    "AWS::NetworkFirewall::LoggingConfiguration": {
        "importProperties": [
            "FirewallArn"
        ]
    },
    "AWS::NetworkFirewall::RuleGroup": {
        "importProperties": [
            "RuleGroupArn"
        ]
    },
    "AWS::NetworkManager::CustomerGatewayAssociation": {
        "importProperties": [
            "GlobalNetworkId",
            "CustomerGatewayArn"
        ]
    },
    "AWS::NetworkManager::Device": {
        "importProperties": [
            "GlobalNetworkId",
            "DeviceId"
        ]
    },
    "AWS::NetworkManager::GlobalNetwork": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::NetworkManager::Link": {
        "importProperties": [
            "GlobalNetworkId",
            "LinkId"
        ]
    },
    "AWS::NetworkManager::LinkAssociation": {
        "importProperties": [
            "GlobalNetworkId",
            "DeviceId",
            "LinkId"
        ]
    },
    "AWS::NetworkManager::Site": {
        "importProperties": [
            "GlobalNetworkId",
            "SiteId"
        ]
    },
    "AWS::NetworkManager::TransitGatewayRegistration": {
        "importProperties": [
            "GlobalNetworkId",
            "TransitGatewayArn"
        ]
    },
    "AWS::OpsWorksCM::Server": {
        "importProperties": [
            "ServerName"
        ]
    },
    "AWS::QLDB::Stream": {
        "importProperties": [
            "LedgerName",
            "Id"
        ]
    },
    "AWS::RDS::DBCluster": {
        "importProperties": [
            "DBClusterIdentifier"
        ]
    },
    "AWS::RDS::DBInstance": {
        "importProperties": [
            "DBInstanceIdentifier"
        ]
    },
    "AWS::RDS::DBProxy": {
        "importProperties": [
            "DBProxyName"
        ]
    },
    "AWS::RDS::DBProxyTargetGroup": {
        "importProperties": [
            "TargetGroupArn"
        ]
    },
    "AWS::RDS::GlobalCluster": {
        "importProperties": [
            "GlobalClusterIdentifier"
        ]
    },
    "AWS::ResourceGroups::Group": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::Route53::DNSSEC": {
        "importProperties": [
            "HostedZoneId"
        ]
    },
    "AWS::Route53::HealthCheck": {
        "importProperties": [
            "HealthCheckId"
        ]
    },
    "AWS::Route53::HostedZone": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Route53::KeySigningKey": {
        "importProperties": [
            "HostedZoneId",
            "Name"
        ]
    },
    "AWS::Route53Resolver::ResolverDNSSECConfig": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Route53Resolver::ResolverQueryLoggingConfig": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::Route53Resolver::ResolverQueryLoggingConfigAssociation": {
        "importProperties": [
            "Id"
        ]
    },
    "AWS::S3::AccessPoint": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::S3::Bucket": {
        "importProperties": [
            "BucketName"
        ]
    },
    "AWS::SES::ConfigurationSet": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::SNS::Topic": {
        "importProperties": [
            "TopicArn"
        ]
    },
    "AWS::SQS::Queue": {
        "importProperties": [
            "QueueUrl"
        ]
    },
    "AWS::SSM::Association": {
        "importProperties": [
            "AssociationId"
        ]
    },
    "AWS::SSO::InstanceAccessControlAttributeConfiguration": {
        "importProperties": [
            "InstanceArn"
        ]
    },
    "AWS::SSO::PermissionSet": {
        "importProperties": [
            "InstanceArn",
            "PermissionSetArn"
        ]
    },
    "AWS::SageMaker::DataQualityJobDefinition": {
        "importProperties": [
            "JobDefinitionArn"
        ]
    },
    "AWS::SageMaker::Device": {
        "importProperties": [
            "DeviceFleetName"
        ]
    },
    "AWS::SageMaker::DeviceFleet": {
        "importProperties": [
            "DeviceFleetName"
        ]
    },
    "AWS::SageMaker::ModelBiasJobDefinition": {
        "importProperties": [
            "JobDefinitionArn"
        ]
    },
    "AWS::SageMaker::ModelExplainabilityJobDefinition": {
        "importProperties": [
            "JobDefinitionArn"
        ]
    },
    "AWS::SageMaker::ModelPackageGroup": {
        "importProperties": [
            "ModelPackageGroupArn"
        ]
    },
    "AWS::SageMaker::ModelQualityJobDefinition": {
        "importProperties": [
            "JobDefinitionArn"
        ]
    },
    "AWS::SageMaker::MonitoringSchedule": {
        "importProperties": [
            "MonitoringScheduleArn"
        ]
    },
    "AWS::SageMaker::Pipeline": {
        "importProperties": [
            "PipelineName"
        ]
    },
    "AWS::SageMaker::Project": {
        "importProperties": [
            "ProjectArn"
        ]
    },
    "AWS::ServiceCatalog::CloudFormationProvisionedProduct": {
        "importProperties": [
            "ProvisionedProductId"
        ]
    },
    "AWS::Signer::ProfilePermission": {
        "importProperties": [
            "StatementId",
            "ProfileName"
        ]
    },
    "AWS::Signer::SigningProfile": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::StepFunctions::StateMachine": {
        "importProperties": [
            "Arn"
        ]
    },
    "AWS::Synthetics::Canary": {
        "importProperties": [
            "Name"
        ]
    },
    "AWS::Timestream::Database": {
        "importProperties": [
            "DatabaseName"
        ]
    },
    "AWS::Timestream::Table": {
        "importProperties": [
            "DatabaseName",
            "TableName"
        ]
    },
    "AWS::WAFv2::IPSet": {
        "importProperties": [
            "Name",
            "Id",
            "Scope"
        ]
    },
    "AWS::WAFv2::RegexPatternSet": {
        "importProperties": [
            "Name",
            "Id",
            "Scope"
        ]
    },
    "AWS::WAFv2::RuleGroup": {
        "importProperties": [
            "Name",
            "Id",
            "Scope"
        ]
    },
    "AWS::WAFv2::WebACL": {
        "importProperties": [
            "Name",
            "Id",
            "Scope"
        ]
    },
    "AWS::WAFv2::WebACLAssociation": {
        "importProperties": [
            "ResourceArn",
            "WebACLArn"
        ]
    },
    "AWS::WorkSpaces::ConnectionAlias": {
        "importProperties": [
            "AliasId"
        ]
    },
    "AWS::CloudFormation::Stack": {
        "importProperties": [
            "StackId"
        ],
        "capabilities": [
            "CAPABILITY_NAMED_IAM"
        ]
    },
    "AWS::IAM::Group": {
        "importProperties": [
            "GroupName"
        ],
        "capabilities": [
            "CAPABILITY_NAMED_IAM"
        ]
    },
    "AWS::IAM::InstanceProfile": {
        "importProperties": [
            "InstanceProfileName"
        ],
        "capabilities": [
            "CAPABILITY_NAMED_IAM"
        ]
    },
    "AWS::IAM::Role": {
        "importProperties": [
            "RoleName"
        ],
        "capabilities": [
            "CAPABILITY_NAMED_IAM"
        ]
    },
    "AWS::IAM::User": {
        "importProperties": [
            "UserName"
        ],
        "capabilities": [
            "CAPABILITY_NAMED_IAM"
        ]
    },
    "AWS::IAM::ManagedPolicy": {
        "importProperties": [
            "PolicyArn"
        ],
        "capabilities": [
            "CAPABILITY_NAMED_IAM"
        ]
    }
}

if len(sys.argv) == 4:
    cfnclient = boto3.client('cloudformation', region_name=sys.argv[3])
elif len(sys.argv) == 3:
    cfnclient = boto3.client('cloudformation')
else:
    print("Inconsistent arguments")
    quit()

try:
    stacks = cfnclient.describe_stacks(
        StackName=sys.argv[1]
    )['Stacks']
except:
    print("Could not find stack")
    quit()

original_stack_id = stacks[0]['StackId']
stack_name = stacks[0]['StackName']
new_stack_name = sys.argv[2]
stack_params = []
if 'Parameters' in stacks[0]:
    stack_params = stacks[0]['Parameters']

original_template = cfnclient.get_template(
    StackName=original_stack_id,
    TemplateStage='Processed'
)['TemplateBody']

if not isinstance(original_template, str):
    original_template = json.dumps(dict(original_template)) # OrderedDict

print("Found stack, detecting drift...")

stack_drift_detection_id = cfnclient.detect_stack_drift(
    StackName=original_stack_id
)['StackDriftDetectionId']

stack_drift_detection_status = cfnclient.describe_stack_drift_detection_status( # no waiter :(
    StackDriftDetectionId=stack_drift_detection_id
)
while stack_drift_detection_status['DetectionStatus'] == "DETECTION_IN_PROGRESS":
    time.sleep(5)
    stack_drift_detection_status = cfnclient.describe_stack_drift_detection_status(
        StackDriftDetectionId=stack_drift_detection_id
    )

if stack_drift_detection_status['DetectionStatus'] != "DETECTION_COMPLETE" or stack_drift_detection_status['StackDriftStatus'] != "DRIFTED":
    if stack_drift_detection_status['StackDriftStatus'] != "IN_SYNC":
        print("Could not determine drift results")
        quit()

resource_drifts = []
resource_drifts_result = cfnclient.describe_stack_resource_drifts(
    StackName=original_stack_id,
    StackResourceDriftStatusFilters=[
        'IN_SYNC',
        'MODIFIED',
        'DELETED',
        'NOT_CHECKED'
    ],
    MaxResults=100
)
resource_drifts += resource_drifts_result['StackResourceDrifts']
while 'NextToken' in resource_drifts_result:
    resource_drifts_result = cfnclient.describe_stack_resource_drifts(
        StackName=original_stack_id,
        StackResourceDriftStatusFilters=[
            'IN_SYNC',
            'MODIFIED',
            'DELETED',
            'NOT_CHECKED'
        ],
        NextToken=resource_drifts_result['NextToken'],
        MaxResults=100
    )
    resource_drifts += resource_drifts_result['StackResourceDrifts']

template = json.loads(to_json(original_template))

# check all is in drift results
for k, v in template['Resources'].items():
    found = False
    for i in range(len(resource_drifts)):
        if resource_drifts[i]['LogicalResourceId'] == k:
            found = True
            break
    if not found:
        print("Found resource type without drift info: " + template['Resources'][k]['Type'] + ", aborting")
        quit()
    if template['Resources'][k]['Type'] not in eligible_import_resources.keys():
        print("Found non-importable resource type: " + template['Resources'][k]['Type'] + ", aborting")
        quit()

for k, v in template['Resources'].items():
    template['Resources'][k]['DeletionPolicy'] = 'Retain'

print("Setting resource retention...")

cfnclient.update_stack(
    StackName=original_stack_id,
    TemplateBody=json.dumps(template),
    Capabilities=[
        'CAPABILITY_NAMED_IAM',
        'CAPABILITY_AUTO_EXPAND'
    ],
    Parameters=stack_params
)

waiter = cfnclient.get_waiter('stack_update_complete')
waiter.wait(
    StackName=original_stack_id,
    WaiterConfig={
        'Delay': 10,
        'MaxAttempts': 360
    }
)

import_resources = []
for drifted_resource in resource_drifts:
    resource_identifier = {}

    import_properties = eligible_import_resources[drifted_resource['ResourceType']]['importProperties'].copy()
    if 'PhysicalResourceIdContext' in drifted_resource:
        for prop in drifted_resource['PhysicalResourceIdContext']:
            if prop['Key'] in import_properties:
                resource_identifier[prop['Key']] = prop['Value']
                import_properties.remove(prop['Key'])
    
    if len(import_properties) > 1:
        print("ERROR: Unexpected additional importable keys required, aborting...")
        quit()
    elif len(import_properties) == 1:
        resource_identifier[import_properties[0]] = drifted_resource['PhysicalResourceId']

    template['Resources'][drifted_resource['LogicalResourceId']] = {
        'DeletionPolicy': 'Retain',
        'Type': drifted_resource['ResourceType'],
        'Properties': json.loads(drifted_resource['ActualProperties'])
    }

    import_resources.append({
        'ResourceType': drifted_resource['ResourceType'],
        'LogicalResourceId': drifted_resource['LogicalResourceId'],
        'ResourceIdentifier': resource_identifier
    })

print("Removing original stack (whilst retaining resources!)...")

cfnclient.delete_stack(
    StackName=original_stack_id
)

waiter = cfnclient.get_waiter('stack_delete_complete')
waiter.wait(
    StackName=original_stack_id,
    WaiterConfig={
        'Delay': 10,
        'MaxAttempts': 360
    }
)

print("Recreating stack with imported resources...")

change_set_name = 'Stack-Rename-' + str(int(time.time()))
new_stack_id = cfnclient.create_change_set(
    StackName=new_stack_name,
    ChangeSetName=change_set_name,
    TemplateBody=json.dumps(template),
    ChangeSetType='IMPORT',
    Capabilities=[
        'CAPABILITY_NAMED_IAM',
        'CAPABILITY_AUTO_EXPAND'
    ],
    ResourcesToImport=import_resources,
    Parameters=stack_params
)['StackId']

waiter = cfnclient.get_waiter('change_set_create_complete')
waiter.wait(
    StackName=new_stack_id,
    ChangeSetName=change_set_name,
    WaiterConfig={
        'Delay': 10,
        'MaxAttempts': 360
    }
)

cfnclient.execute_change_set(
    ChangeSetName=change_set_name,
    StackName=new_stack_id
)

waiter = cfnclient.get_waiter('stack_import_complete')
waiter.wait(
    StackName=new_stack_id,
    WaiterConfig={
        'Delay': 10,
        'MaxAttempts': 360
    }
)

print("Cleaning up...")

cfnclient.update_stack(
    StackName=new_stack_id,
    TemplateBody=original_template,
    Capabilities=[
        'CAPABILITY_NAMED_IAM',
        'CAPABILITY_AUTO_EXPAND'
    ],
    Parameters=stack_params
)

waiter = cfnclient.get_waiter('stack_update_complete')
waiter.wait(
    StackName=new_stack_id,
    WaiterConfig={
        'Delay': 10,
        'MaxAttempts': 360
    }
)

print("Succcessfully renamed stack")
