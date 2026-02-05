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

UCLASS(BlueprintType)
class UFlowerController : public UObject
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable)
	void Init(const FFlowerControllerConfig& Config);
	
	UFUNCTION(BlueprintCallable)
	void SendFlowerRotation(const FOSCAddress& Address, float Rotation) const;
	
private:
	UPROPERTY(Transient)
	TObjectPtr<UOSCClient> OscClient;
};
