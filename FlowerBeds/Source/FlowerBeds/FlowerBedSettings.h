#pragma once

#include "CoreMinimal.h"
#include "OSCAddress.h"

#include "FlowerBedSettings.generated.h"

USTRUCT(BlueprintType)
struct FFlowerClusterConfig
{
	GENERATED_BODY()
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	FVector ModuleRelativePosCm = FVector::ZeroVector;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	FOSCAddress OscAddress;
};

USTRUCT(BlueprintType)
struct FFollowerModuleConfig
{
	GENERATED_BODY()
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	FVector LeaderRelativePosCm = FVector::ZeroVector;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	TArray<FFlowerClusterConfig> FlowerClusters;
};

USTRUCT(BlueprintType)
struct FLeaderModuleConfig
{
	GENERATED_BODY()
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	FString IPAddress;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	int32 Port = 0;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	FVector PosCm = FVector::ZeroVector;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	TArray<FFlowerClusterConfig> FlowerClusters;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	TArray<FFollowerModuleConfig> Followers;
};

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Flower Bed Settings"))
class FLOWERBEDS_API UFlowerBedSettings : public UDeveloperSettings
{
	GENERATED_BODY()
	
	public:
		UPROPERTY(EditAnywhere, Config, Category = "Flower Beds")
		TArray<FLeaderModuleConfig> LeaderModules;
};
