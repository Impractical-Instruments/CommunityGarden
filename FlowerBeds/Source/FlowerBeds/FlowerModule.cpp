#include "FlowerModule.h"

void AFlowerModule::Init(const FFlowerModuleConfig& Config)
{
	SetActorLocation(Config.RegistrationPointPosCm);
	SetActorRotation(Config.Rotation);
	
	for (const auto& ClusterConfig : Config.FlowerClusters)
	{
		FActorSpawnParameters SpawnParams;
		SpawnParams.Owner = this;
		AFlowerCluster* SpawnedActor = GetWorld()->SpawnActor<AFlowerCluster>(
			FlowerClusterClass,
			FVector::ZeroVector,
			FRotator::ZeroRotator,
			SpawnParams);
		SpawnedActor->AttachToActor(this, FAttachmentTransformRules::KeepRelativeTransform);
		SpawnedActor->Init(ClusterConfig);
		FlowerClusters.Add(SpawnedActor);
	}
}

void AFlowerModule::UpdateClusterTargets(
	const TArray<FVector>& Targets,
	TArray<AFlowerCluster::FUpdateTargetResult>& Results) const
{
	for (const auto& Cluster : FlowerClusters)
	{
		Results.Add(Cluster->UpdateClusterTargets(Targets));
	}
}
