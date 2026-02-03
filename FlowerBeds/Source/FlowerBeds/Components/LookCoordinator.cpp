#include "LookCoordinator.h"

#include "FlowerBedsWorldSettings.h"
#include "LookCoordinatorConfig.h"

void ULookCoordinator::RegisterLooker(AActor* Looker)
{
	if (LookerStates.ContainsByPredicate(
		[Looker](const FLookerState& State)
		{
			return State.Looker == Looker;
		}))
	{
		return;
	}
	
	FLookerState NewLookerState;
	NewLookerState.Looker = Looker;
	LookerStates.Emplace(MoveTemp(NewLookerState));
}

void ULookCoordinator::UnregisterLooker(AActor* Looker)
{
	LookerStates.RemoveAllSwap(
		[Looker](const FLookerState& State)
		{
			return State.Looker == Looker;
		});
}

void ULookCoordinator::RegisterAttractor(AActor* Attractor)
{
	Attractors.AddUnique(Attractor);
}

void ULookCoordinator::UnregisterAttractor(AActor* Attractor)
{
	Attractors.RemoveSwap(Attractor);
}

void ULookCoordinator::Deinitialize()
{
	LookerStates.Empty();
	Attractors.Empty();
	
	Super::Deinitialize();
}

TStatId ULookCoordinator::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(ULookCoordinator, STATGROUP_Tickables);
}

void ULookCoordinator::Tick(const float DeltaTime)
{
	Super::Tick(DeltaTime);
	
	UpdateAttractors();
	UpdateLookers();
}

const ULookCoordinatorConfig* ULookCoordinator::GetConfig() const
{
	const UWorld* World = GetWorld();
	
	if (!World)
	{
		return nullptr;
	}
	
	if (const AFlowerBedsWorldSettings* WorldSettings = Cast<AFlowerBedsWorldSettings>(World->GetWorldSettings()))
	{
		return WorldSettings->LookCoordinatorConfig;
	}
	
	return nullptr;
}

void ULookCoordinator::UpdateAttractors()
{
	Attractors.RemoveAllSwap([](const TWeakObjectPtr<AActor>& Attractor)
	{
		return !Attractor.IsValid();
	});
}

void ULookCoordinator::UpdateLookers()
{
	// iterate backward for efficiency and safety when removing elements
	for (int32 i = LookerStates.Num(); --i >= 0;)
	{
		// remove inactive
		if (!LookerStates[i].Looker.IsValid())
		{
			LookerStates.RemoveAtSwap(i);
		}
		// update active
		else
		{
			UpdateLooker(LookerStates[i]);
		}
	}
}

static FRotator GetLookRotation(const FVector& From, const FVector& To)
{
	const FVector LookDir = (To - From).GetSafeNormal();
	const FVector LookYaw = LookDir.VectorPlaneProject(LookDir, FVector::UpVector);
	return LookYaw.Rotation();
}

void ULookCoordinator::UpdateLooker(FLookerState& LookerState)
{
	const FVector LookerLocation = LookerState.Looker->GetActorLocation();
	
	if (LookerState.CurrentTarget.IsValid() && !LookerState.CurrentTarget->IsHidden())
	{
		LookerState.CurrentTargetDistanceSq = 
			FVector::DistSquared(LookerLocation, LookerState.CurrentTarget->GetActorLocation());
	}
	else
	{
		LookerState.CurrentTargetDistanceSq = TNumericLimits<float>::Max();
	}
	
	for (const TWeakObjectPtr<AActor>& Attractor : Attractors)
	{
		if (Attractor->IsHidden())
		{
			continue;
		}
		
		if (const float DistanceSq = FVector::DistSquared(LookerLocation, Attractor->GetActorLocation()); 
			DistanceSq < LookerState.CurrentTargetDistanceSq)
		{
			LookerState.CurrentTarget = Attractor;
			LookerState.CurrentTargetDistanceSq = DistanceSq;
		}
	}
	
	if (LookerState.CurrentTarget.IsValid())
	{
		LookerState.Looker->SetActorRotation(
			GetLookRotation(LookerLocation, LookerState.CurrentTarget->GetActorLocation()));
	}
}
