# CloudFormation Stack Rename

The following script will programmatically perform the following steps:

* Get resource import IDs from drift results
* Set all resources in the stack to retain on delete
* Delete the stack, whilst retaining the resource
* Create a new stack, importing the resources with their current state back into the stack

As the stack is recreated entirely, the history of the stack will not be retained. Note that not all stacks will support a stack rename, only those that exclusively contain importable types.

> :exclamation: This script is not thoroughly tested and you should attempt to use this on a non-critical resource before real-world usage as some resources refuse to re-import for a variety of reasons. I am not responsible for your data loss.

## Usage

```
python3 index.py OldStackName NewStackName
```

or to specify a region

```
python3 index.py OldStackName NewStackName us-east-1
```

or to specify a region and profile name

```
python3 index.py OldStackName NewStackName us-east-1 myprofile
```

### Supported Resources

The following resources are supported for stack rename (if other resources are within the stack, the script will refuse to continue):

* AWS::ACMPCA::Certificate
* AWS::ACMPCA::CertificateAuthority
* AWS::ACMPCA::CertificateAuthorityActivation
* AWS::AccessAnalyzer::Analyzer
* AWS::ApiGateway::Authorizer
* AWS::ApiGateway::ClientCertificate
* AWS::ApiGateway::Deployment
* AWS::ApiGateway::DocumentationVersion
* AWS::ApiGateway::DomainName
* AWS::ApiGateway::Method
* AWS::ApiGateway::Model
* AWS::ApiGateway::RequestValidator
* AWS::ApiGateway::Resource
* AWS::ApiGateway::RestApi
* AWS::ApiGateway::Stage
* AWS::AppFlow::ConnectorProfile
* AWS::AppFlow::Flow
* AWS::ApplicationInsights::Application
* AWS::Athena::DataCatalog
* AWS::Athena::NamedQuery
* AWS::Athena::WorkGroup
* AWS::AuditManager::Assessment
* AWS::AutoScaling::AutoScalingGroup
* AWS::AutoScaling::LaunchConfiguration
* AWS::AutoScaling::LifecycleHook
* AWS::AutoScaling::ScalingPolicy
* AWS::AutoScaling::ScheduledAction
* AWS::CE::CostCategory
* AWS::Cassandra::Keyspace
* AWS::Cassandra::Table
* AWS::Chatbot::SlackChannelConfiguration
* AWS::CloudFormation::ModuleDefaultVersion
* AWS::CloudFormation::ModuleVersion
* AWS::CloudFormation::Stack
* AWS::CloudFormation::StackSet
* AWS::CloudFront::CachePolicy
* AWS::CloudFront::KeyGroup
* AWS::CloudFront::OriginRequestPolicy
* AWS::CloudFront::PublicKey
* AWS::CloudFront::RealtimeLogConfig
* AWS::CloudTrail::Trail
* AWS::CloudWatch::Alarm
* AWS::CloudWatch::CompositeAlarm
* AWS::CloudWatch::MetricStream
* AWS::CodeArtifact::Domain
* AWS::CodeArtifact::Repository
* AWS::CodeGuruProfiler::ProfilingGroup
* AWS::CodeGuruReviewer::RepositoryAssociation
* AWS::CodeStarConnections::Connection
* AWS::Config::ConformancePack
* AWS::Config::OrganizationConformancePack
* AWS::Config::StoredQuery
* AWS::DataBrew::Dataset
* AWS::DataBrew::Job
* AWS::DataBrew::Project
* AWS::DataBrew::Recipe
* AWS::DataBrew::Schedule
* AWS::DataSync::Agent
* AWS::DataSync::LocationEFS
* AWS::DataSync::LocationFSxWindows
* AWS::DataSync::LocationNFS
* AWS::DataSync::LocationObjectStorage
* AWS::DataSync::LocationS3
* AWS::DataSync::LocationSMB
* AWS::DataSync::Task
* AWS::Detective::Graph
* AWS::Detective::MemberInvitation
* AWS::DevOpsGuru::NotificationChannel
* AWS::DevOpsGuru::ResourceCollection
* AWS::DynamoDB::Table
* AWS::EC2::CarrierGateway
* AWS::EC2::EIP
* AWS::EC2::FlowLog
* AWS::EC2::GatewayRouteTableAssociation
* AWS::EC2::Instance
* AWS::EC2::InternetGateway
* AWS::EC2::LocalGatewayRoute
* AWS::EC2::LocalGatewayRouteTableVPCAssociation
* AWS::EC2::NatGateway
* AWS::EC2::NetworkAcl
* AWS::EC2::NetworkInsightsAnalysis
* AWS::EC2::NetworkInsightsPath
* AWS::EC2::NetworkInterface
* AWS::EC2::PrefixList
* AWS::EC2::RouteTable
* AWS::EC2::SecurityGroup
* AWS::EC2::Subnet
* AWS::EC2::VPC
* AWS::EC2::Volume
* AWS::ECR::PublicRepository
* AWS::ECR::Repository
* AWS::ECS::CapacityProvider
* AWS::ECS::Cluster
* AWS::ECS::PrimaryTaskSet
* AWS::ECS::Service
* AWS::ECS::TaskDefinition
* AWS::ECS::TaskSet
* AWS::EFS::AccessPoint
* AWS::EFS::FileSystem
* AWS::EKS::FargateProfile
* AWS::ElastiCache::User
* AWS::ElastiCache::UserGroup
* AWS::ElasticLoadBalancing::LoadBalancer
* AWS::ElasticLoadBalancingV2::Listener
* AWS::ElasticLoadBalancingV2::ListenerRule
* AWS::ElasticLoadBalancingV2::LoadBalancer
* AWS::EventSchemas::RegistryPolicy
* AWS::Events::Archive
* AWS::Events::Rule
* AWS::FMS::NotificationChannel
* AWS::FMS::Policy
* AWS::GameLift::Alias
* AWS::GameLift::GameServerGroup
* AWS::GlobalAccelerator::Accelerator
* AWS::GlobalAccelerator::EndpointGroup
* AWS::GlobalAccelerator::Listener
* AWS::Glue::Registry
* AWS::Glue::Schema
* AWS::Glue::SchemaVersion
* AWS::Glue::SchemaVersionMetadata
* AWS::GreengrassV2::ComponentVersion
* AWS::IVS::Channel
* AWS::IVS::PlaybackKeyPair
* AWS::IVS::StreamKey
* AWS::ImageBuilder::Component
* AWS::ImageBuilder::DistributionConfiguration
* AWS::ImageBuilder::Image
* AWS::ImageBuilder::ImagePipeline
* AWS::ImageBuilder::ImageRecipe
* AWS::ImageBuilder::InfrastructureConfiguration
* AWS::IoT::Authorizer
* AWS::IoT::Certificate
* AWS::IoT::DomainConfiguration
* AWS::IoT::ProvisioningTemplate
* AWS::IoT::Thing
* AWS::IoT::TopicRuleDestination
* AWS::IoTSiteWise::AccessPolicy
* AWS::IoTSiteWise::Asset
* AWS::IoTSiteWise::AssetModel
* AWS::IoTSiteWise::Dashboard
* AWS::IoTSiteWise::Gateway
* AWS::IoTSiteWise::Portal
* AWS::IoTSiteWise::Project
* AWS::IoTWireless::Destination
* AWS::IoTWireless::DeviceProfile
* AWS::IoTWireless::ServiceProfile
* AWS::IoTWireless::WirelessDevice
* AWS::IoTWireless::WirelessGateway
* AWS::KMS::Alias
* AWS::KMS::Key
* AWS::Kendra::DataSource
* AWS::Kendra::Faq
* AWS::Kendra::Index
* AWS::Kinesis::Stream
* AWS::KinesisFirehose::DeliveryStream
* AWS::Lambda::Alias
* AWS::Lambda::CodeSigningConfig
* AWS::Lambda::EventSourceMapping
* AWS::Lambda::Function
* AWS::Lambda::Version
* AWS::LicenseManager::Grant
* AWS::LicenseManager::License
* AWS::Logs::LogGroup
* AWS::Logs::MetricFilter
* AWS::Logs::SubscriptionFilter
* AWS::MWAA::Environment
* AWS::Macie::CustomDataIdentifier
* AWS::Macie::FindingsFilter
* AWS::Macie::Session
* AWS::MediaConnect::Flow
* AWS::MediaConnect::FlowEntitlement
* AWS::MediaConnect::FlowOutput
* AWS::MediaConnect::FlowSource
* AWS::MediaConnect::FlowVpcInterface
* AWS::MediaPackage::Asset
* AWS::MediaPackage::Channel
* AWS::MediaPackage::OriginEndpoint
* AWS::MediaPackage::PackagingConfiguration
* AWS::MediaPackage::PackagingGroup
* AWS::NetworkFirewall::Firewall
* AWS::NetworkFirewall::FirewallPolicy
* AWS::NetworkFirewall::LoggingConfiguration
* AWS::NetworkFirewall::RuleGroup
* AWS::NetworkManager::CustomerGatewayAssociation
* AWS::NetworkManager::Device
* AWS::NetworkManager::GlobalNetwork
* AWS::NetworkManager::Link
* AWS::NetworkManager::LinkAssociation
* AWS::NetworkManager::Site
* AWS::NetworkManager::TransitGatewayRegistration
* AWS::OpsWorksCM::Server
* AWS::QLDB::Stream
* AWS::RDS::DBCluster
* AWS::RDS::DBInstance
* AWS::RDS::DBProxy
* AWS::RDS::DBProxyTargetGroup
* AWS::RDS::GlobalCluster
* AWS::ResourceGroups::Group
* AWS::Route53::DNSSEC
* AWS::Route53::HealthCheck
* AWS::Route53::HostedZone
* AWS::Route53::KeySigningKey
* AWS::Route53Resolver::ResolverDNSSECConfig
* AWS::Route53Resolver::ResolverQueryLoggingConfig
* AWS::Route53Resolver::ResolverQueryLoggingConfigAssociation
* AWS::S3::AccessPoint
* AWS::S3::Bucket
* AWS::SES::ConfigurationSet
* AWS::SNS::Topic
* AWS::SQS::Queue
* AWS::SSM::Association
* AWS::SSO::InstanceAccessControlAttributeConfiguration
* AWS::SSO::PermissionSet
* AWS::SageMaker::DataQualityJobDefinition
* AWS::SageMaker::Device
* AWS::SageMaker::DeviceFleet
* AWS::SageMaker::ModelBiasJobDefinition
* AWS::SageMaker::ModelExplainabilityJobDefinition
* AWS::SageMaker::ModelPackageGroup
* AWS::SageMaker::ModelQualityJobDefinition
* AWS::SageMaker::MonitoringSchedule
* AWS::SageMaker::Pipeline
* AWS::SageMaker::Project
* AWS::ServiceCatalog::CloudFormationProvisionedProduct
* AWS::Signer::ProfilePermission
* AWS::Signer::SigningProfile
* AWS::StepFunctions::StateMachine
* AWS::Synthetics::Canary
* AWS::Timestream::Database
* AWS::Timestream::Table
* AWS::WAFv2::IPSet
* AWS::WAFv2::RegexPatternSet
* AWS::WAFv2::RuleGroup
* AWS::WAFv2::WebACL
* AWS::WAFv2::WebACLAssociation
* AWS::WorkSpaces::ConnectionAlias
* AWS::IAM::Group
* AWS::IAM::InstanceProfile
* AWS::IAM::Role
* AWS::IAM::User
* AWS::IAM::ManagedPolicy

### Known Issues

* Stacks that have an `Fn::ImportValue` reference against it will cause the stack to be unable to be deleted
* Some transforms may affect the RetainPolicy - check if this affects you before executing
