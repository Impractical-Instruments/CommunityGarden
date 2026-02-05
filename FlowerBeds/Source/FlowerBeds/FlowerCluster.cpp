#include "FlowerCluster.h"

void AFlowerCluster::Init(const FFlowerClusterConfig& Config)
{
	SetActorRelativeLocation(Config.PosOffsetCm);
	SetActorRelativeRotation(Config.RotationOffset);
	
	OscAddress = Config.OscAddress;
}

static FRotator GetLookRotation(const FVector& From, const FVector& To)
{
	const FVector LookDir = (To - From).GetSafeNormal();
	const FVector LookYaw = LookDir.VectorPlaneProject(LookDir, FVector::UpVector);
	return LookYaw.Rotation();
}

AFlowerCluster::FUpdateTargetResult AFlowerCluster::UpdateClusterTargets(const TArray<FVector>& Targets)
{
	bool HasTarget = false;
	FVector ClosestTarget;
	float ClosestDistanceSq = TNumericLimits<float>::Max();
	
	for (const FVector& Target : Targets)
	{
		const float DistanceSq = FVector::DistSquared(GetActorLocation(), Target);
		
		if (DistanceSq < ClosestDistanceSq)
		{
			ClosestDistanceSq = DistanceSq;
			ClosestTarget = Target;
			HasTarget = true;
		}
	}
	
	if (!HasTarget)
	{
		return FUpdateTargetResult();
	}
	
	FUpdateTargetResult Result;
	Result.OscAddress = OscAddress;
	Result.HasTarget = true;
	
	const FRotator LookRotation = GetLookRotation(GetActorLocation(), ClosestTarget);
	SetActorRotation(LookRotation);
	
	Result.Rotation = LookRotation.Yaw;
	
	return Result;
}
