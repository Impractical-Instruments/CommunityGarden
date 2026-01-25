#pragma once

#include "CoreMinimal.h"

// We include the Orbbec SDK headers in the private implementation to avoid leaking them to everything that includes this header
// unless we really need to. But for the public API, we might need some types.
// For now, let's use forward declarations or simple types.

#include "OrbbecCameraController.generated.h"

UENUM(BlueprintType)
enum class EOrbbecFrameFormat : uint8
{
	YUYV,
	MJPG,
	Y16,
	RGB,
	BGR,
	BGRA,
	RGBA,
	Unknown
};

USTRUCT(BlueprintType)
struct ORBBECSENSOR_API FOrbbecVideoConfig
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Width = 0; // 0 means default/any

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Height = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 FPS = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	EOrbbecFrameFormat Format = EOrbbecFrameFormat::Unknown;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FOnOrbbecFrameReceived, const TArray<uint8>&, Data, int32, Width, int32, Height, EOrbbecFrameFormat, Format);

/**
 * Class to configure and get streams from an Orbbec camera.
 */
UCLASS(BlueprintType)
class ORBBECSENSOR_API UOrbbecCameraController : public UObject
{
	GENERATED_BODY()

public:
	UOrbbecCameraController();
	virtual ~UOrbbecCameraController() override;
	
	// Required for UObject with pimpl pattern - must be defined in .cpp
	UOrbbecCameraController(FVTableHelper& Helper);

	/** Starts the camera with the specified configuration. */
	UFUNCTION(BlueprintCallable, Category = "Orbbec")
	bool StartCamera(const FOrbbecVideoConfig& ColorConfig, const FOrbbecVideoConfig& DepthConfig, const FOrbbecVideoConfig& IRConfig);

	/** Stops the camera. */
	UFUNCTION(BlueprintCallable, Category = "Orbbec")
	void StopCamera();

	UPROPERTY(BlueprintAssignable, Category = "Orbbec")
	FOnOrbbecFrameReceived OnColorFrameReceived;

	UPROPERTY(BlueprintAssignable, Category = "Orbbec")
	FOnOrbbecFrameReceived OnDepthFrameReceived;

	UPROPERTY(BlueprintAssignable, Category = "Orbbec")
	FOnOrbbecFrameReceived OnIRFrameReceived;

private:
	// Implementation details hidden in the cpp file to avoid SDK header pollution
	struct FOrbbecImplementation;
	TUniquePtr<FOrbbecImplementation> Implementation;
};
