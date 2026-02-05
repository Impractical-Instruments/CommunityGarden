#pragma once

#include "CoreMinimal.h"
#include "FlowerController.h"
#include "FlowerModule.h"

#include "FlowerBedSettings.generated.h"

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Flower Bed Settings"))
class FLOWERBEDS_API UFlowerBedSettings : public UDeveloperSettings
{
	GENERATED_BODY()
	
public:
	/**
	 * The motor control units that control the modules.
	 * NB: Physically, these may be part of a module, but we treat them as logically separate so we can change
	 * construction and wiring as necessary.
	 */
	UPROPERTY(EditAnywhere, Config, Category = "Flower Beds")
	TArray<FFlowerControllerConfig> FlowerControllers;

	/**
	 * The modules, which contain some number of flower clusters.
	 */
	UPROPERTY(EditAnywhere, Config, Category = "Flower Beds")
	TArray<FFlowerModuleConfig> FlowerModules;
};
