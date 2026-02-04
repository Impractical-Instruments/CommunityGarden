#pragma once

#include "CoreMinimal.h"

#include "LookCoordinator.generated.h"

class ULookCoordinatorConfig;

UCLASS(ClassGroup = (FlowerBeds))
class ULookCoordinator : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable)
	void RegisterLooker(AActor* Looker);
	
	UFUNCTION(BlueprintCallable)
	void UnregisterLooker(AActor* Looker);
	
	UFUNCTION(BlueprintCallable)
	void RegisterAttractor(AActor* Attractor);
	
	UFUNCTION(BlueprintCallable)
	void UnregisterAttractor(AActor* Attractor);
	
	virtual void Deinitialize() override;
	virtual TStatId GetStatId() const override;
	virtual void Tick(float DeltaTime) override;
	
private:
	UPROPERTY(Transient)
	TArray<TWeakObjectPtr<AActor>> Attractors{};
	
	void UpdateAttractors();
	
	struct FLookerState
	{
		TWeakObjectPtr<AActor> Looker;
		TWeakObjectPtr<AActor> CurrentTarget;
		float CurrentTargetDistanceSq = TNumericLimits<float>::Max();
	};
	
	TArray<FLookerState> LookerStates{};
	
	void UpdateLookers();
	void UpdateLooker(FLookerState& LookerState);
};
