#pragma once

#include "CoreMinimal.h"
#include "OSCAddress.h"

#include "FlowerCluster.generated.h"

USTRUCT(BlueprintType)
struct FFlowerClusterConfig
{
	GENERATED_BODY()

	/**
	 * The position of the flower cluster relative to the module's registration point.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	FVector PosOffsetCm = FVector::ZeroVector;

	/**
	 * The rotation offset of this cluster relative to its module.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	FRotator RotationOffset = FRotator::ZeroRotator;

	/**
	 * The id of the motor that this cluster drives
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	uint8 MotorId = 0;
};

UCLASS(ClassGroup = (FlowerBeds))
class AFlowerCluster : public AActor
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	uint8 MotorId;
	
	UFUNCTION(BlueprintCallable)
	void Init(const FFlowerClusterConfig& Config);
	
	struct FUpdateTargetResult
	{
		bool HasTarget = false;
		uint8 MotorId;
		float Rotation;
	};
	
	FUpdateTargetResult UpdateClusterTargets(const TArray<FVector>& Targets);
};
