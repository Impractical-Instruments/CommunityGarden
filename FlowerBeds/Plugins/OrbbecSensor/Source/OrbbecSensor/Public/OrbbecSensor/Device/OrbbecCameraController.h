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

UENUM()
enum class EOrbbecSensorType : uint8
{
	IR,
	Color,
	Depth,
	IRLeft,
	IRRight,
	ColorLeft,
	ColorRight,
	Unknown
};

USTRUCT(BlueprintType)
struct ORBBECSENSOR_API FOrbbecVideoConfig
{
	GENERATED_BODY()

	/**
	 * Sensor type (IR, Color, Depth, etc.)
	 */
	UPROPERTY(editAnywhere, BlueprintReadWrite, Category = "Orbbec")
	EOrbbecSensorType SensorType = EOrbbecSensorType::Unknown;
	
	/**
	 * Frame format to request.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	EOrbbecFrameFormat Format = EOrbbecFrameFormat::Unknown;
	
	/**
	 * Camera video frame width. 0 means default/any
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Width = 0; // 0 means default/any

	/**
	 * Camera video frame width. 0 means default/any
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Height = 0;

	/**
	 * Camera video framerate. 0 means default/any
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	int32 Framerate = 0;

	/**
	 * The texture to update
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	UTexture2D* Texture = nullptr;
};

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

	/**
	 * The serial number of the connected Orbbec camera device. Optional, but necessary to support multiple devices.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	FString DeviceSerialNumber;
	
	/**
	 * The video stream configurations to use when calling StartCamera()
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Orbbec")
	TArray<FOrbbecVideoConfig> VideoConfigs;

private:
	// Implementation details hidden in the cpp file to avoid SDK header pollution
	class FOrbbecImplementation;
	TUniquePtr<FOrbbecImplementation> Implementation;
};
