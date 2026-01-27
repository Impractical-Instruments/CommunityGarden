#pragma once

#include "CoreMinimal.h"

// We include the Orbbec SDK headers in the private implementation to avoid leaking them to everything that includes this header
// unless we really need to. But for the public API, we might need some types.
// For now, let's use forward declarations or simple types.

#include "OrbbecCameraController.generated.h"

UENUM()
enum class EOrbbecSensorType : uint8
{
	IR,
	Color,
	Depth,
	Unknown
};

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

	/**
	 * Whether this stream should be enabled
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	bool bEnabled = false;
	
	/**
	 * Frame format to request.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	EOrbbecFrameFormat Format = EOrbbecFrameFormat::Unknown;
	
	/**
	 * Camera video frame width.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Width = 0;

	/**
	 * Camera video frame width.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Height = 0;

	/**
	 * Camera video framerate.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Framerate = 0;
};

USTRUCT(BlueprintType)
struct FOrbbecFrame
{
	GENERATED_BODY()
	
	UPROPERTY(BlueprintReadOnly)
	FOrbbecVideoConfig Config{};
	
	UPROPERTY(BlueprintReadOnly)
	TArray<uint8> Data{};
	
	UPROPERTY(BlueprintReadOnly)
	uint64 TimestampUs = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(
	FOrbbecFramesReceived, 
	const FOrbbecFrame&, ColorFrame, 
	const FOrbbecFrame&, DepthFrame, 
	const FOrbbecFrame&, IRFrame);

/**
 * Class to configure and get streams from an Orbbec camera.
 */
UCLASS(ClassGroup = (Orbbec), meta = (BlueprintSpawnableComponent))
class ORBBECSENSOR_API UOrbbecCameraController : public UActorComponent
{
	GENERATED_BODY()

public:
	UOrbbecCameraController();
	virtual ~UOrbbecCameraController() override;
	
	// Required for UObject with pimpl pattern - must be defined in .cpp
	explicit UOrbbecCameraController(FVTableHelper& Helper);

	/** 
	 * Starts the camera with the specified configuration. 
	 */
	UFUNCTION(BlueprintCallable, Category = "Orbbec")
	bool StartCamera();

	/** 
	 * Stops the camera.
	 */
	UFUNCTION(BlueprintCallable, Category = "Orbbec")
	void StopCamera();
	
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * The serial number of the connected Orbbec camera device. Optional, but necessary to support multiple devices.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	FString DeviceSerialNumber;
	
	/**
	 * The color video stream config, if desired
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	FOrbbecVideoConfig ColorConfig;

	/**
	 * The depth video stream config, if desired
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	FOrbbecVideoConfig DepthConfig;

	/**
	 * The IR video stream config, if desired
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	FOrbbecVideoConfig IRConfig;

	/**
	 * This gets called when new frames are received from the camera
	 */
	UPROPERTY(BlueprintAssignable, Category = "Orbbec")
	FOrbbecFramesReceived OnFramesReceived;

private:
	// Implementation details hidden in the cpp file to avoid SDK header pollution
	class FOrbbecImplementation;
	TSharedPtr<FOrbbecImplementation> Implementation;
	
	FOrbbecFrame LatestColorFrame;
	FOrbbecFrame LatestDepthFrame;
	FOrbbecFrame LatestIRFrame;
};
