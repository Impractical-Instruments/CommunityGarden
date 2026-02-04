#pragma once

#include "CoreMinimal.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"

#include "BlobTrackerSettings.generated.h"

USTRUCT(BlueprintType)
struct FBlobTrackerConfig
{
	GENERATED_BODY()
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BlobTracker")
	FName Name = NAME_None;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BlobTracker")
	FVector PosCm = FVector::ZeroVector;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BlobTracker")
	FRotator Rotation = FRotator::ZeroRotator;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "BlobTracker")
	FOrbbecCameraConfig CameraConfig;
};

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Blob Tracker Settings"))
class UBlobTrackerSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Config, Category = "BlobTracker")
	TArray<FBlobTrackerConfig> BlobTrackers;
};
