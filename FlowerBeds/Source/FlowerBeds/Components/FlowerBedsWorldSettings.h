#pragma once

#include "CoreMinimal.h"

#include "FlowerBedsWorldSettings.generated.h"

class ULookCoordinatorConfig;

UCLASS()
class AFlowerBedsWorldSettings : public AWorldSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Look Coordinator")
	TObjectPtr<ULookCoordinatorConfig> LookCoordinatorConfig;
};
