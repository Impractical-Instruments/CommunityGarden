#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"

#include "TouchScreenSettings.generated.h"

USTRUCT(BlueprintType)
struct FTouchScreenConfig
{
	GENERATED_BODY()

	/**
	 * Logical name identifying this screen. Matched against ATouchScreen::ScreenName at runtime.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	FName Name = NAME_None;

	/**
	 * World-space position of the Orbbec camera observing this screen (cm).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	FVector CameraPosCm = FVector::ZeroVector;

	/**
	 * Rotation of the camera. +X faces into the scene (toward the screen surface).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	FRotator CameraRotation = FRotator::ZeroRotator;

	/**
	 * World-space position of the centre of the physical screen surface (cm).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	FVector ScreenPosCm = FVector::ZeroVector;

	/**
	 * Orientation of the screen surface. +X is the outward-facing normal (toward the viewer),
	 * +Y is screen-right, +Z is screen-up.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	FRotator ScreenRotation = FRotator::ZeroRotator;

	/**
	 * Physical width of the projected screen area (cm).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	float WidthCm = 100.f;

	/**
	 * Physical height of the projected screen area (cm).
	 * Default is approximately 6 feet (183 cm).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	float HeightCm = 183.f;

	/**
	 * How close (cm) a depth-camera point must be in front of the screen plane to
	 * register as a touch. Tune this for the physical screen and camera setup.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	float TouchThresholdCm = 5.f;

	/**
	 * Orbbec camera configuration. Depth stream must be enabled; colour and IR are optional.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Config, Category = "Touch Screen")
	FOrbbecCameraConfig CameraConfig;
};

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Touch Screen Settings"))
class FLOWERBEDS_API UTouchScreenSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Config, Category = "Touch Screen")
	TArray<FTouchScreenConfig> TouchScreens;
};
