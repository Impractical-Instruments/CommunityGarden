#pragma once

#include "CoreMinimal.h"
#include "FlowerCluster.h"

#include "FlowerModule.generated.h"

USTRUCT(BlueprintType)
struct FFlowerModuleConfig
{
	GENERATED_BODY()
	
	/**
	 * The position of the registration mark on the module, relative to wherever you chose to be the world origin.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	FVector RegistrationPointPosCm = FVector::ZeroVector;

	/**
	 * The rotation of the module relative to its default orientation (registration point at bottom left from top view)
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	FRotator Rotation = FRotator::ZeroRotator;
	
	/**
	 * The flower clusters that are part of this module.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	TArray<FFlowerClusterConfig> FlowerClusters;
};

UCLASS(ClassGroup = (FlowerBeds))
class AFlowerModule : public AActor
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	TSubclassOf<AFlowerCluster> FlowerClusterClass;
	
	UFUNCTION(BlueprintCallable)
	void Init(const FFlowerModuleConfig& Config);
	
	void UpdateClusterTargets(const TArray<FVector>& Targets, TArray<AFlowerCluster::FUpdateTargetResult>& Results) const;
	
private:
	UPROPERTY(Transient)
	TArray<TObjectPtr<AFlowerCluster>> FlowerClusters;
};
