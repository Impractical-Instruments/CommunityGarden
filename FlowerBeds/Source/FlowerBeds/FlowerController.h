#pragma once

#include "CoreMinimal.h"
#include "OSCAddress.h"

#include "FlowerController.generated.h"

class UOSCClient;

USTRUCT(BlueprintType)
struct FFlowerControllerConfig
{
	GENERATED_BODY()

	/**
	 * The IP address of the controller.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	FString IPAddress;

	/**
	 * The port to use for communication with the controller.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Flower Beds")
	int32 Port = 0;
};

// OSC address used to command a flower rotation.
// Must match OSC_FLOWER_ROTATION in the Arduino firmware
// (Firmware/FlowerBeds_Follow_ServoController/FlowerBeds_Follow_ServoController.ino).
inline constexpr const TCHAR* FlowerRotationOSCAddress = TEXT("/cg/ff/rot");

UCLASS(BlueprintType)
class UFlowerController : public UObject
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable)
	void Init(const FFlowerControllerConfig& Config);
	
	UFUNCTION(BlueprintCallable)
	void SendFlowerRotation(uint8 MotorId, float Rotation) const;
	
private:
	UPROPERTY(Transient)
	TObjectPtr<UOSCClient> OscClient;
};
