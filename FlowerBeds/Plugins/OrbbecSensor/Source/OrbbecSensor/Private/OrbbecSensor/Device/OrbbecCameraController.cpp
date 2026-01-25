#include "OrbbecSensor/Device/OrbbecCameraController.h"

#include "RHI.h"
#include "Async/Async.h"
#include "Engine/Texture2D.h"

#include "OrbbecSensor/OrbbecSensorModule.h"

// Disable overzealous strncpy warnign
#if PLATFORM_WINDOWS
  #pragma warning(push)
  #pragma warning(disable : 4996)
#endif

#include <libobsensor/ObSensor.hpp>

#if PLATFORM_WINDOWS
  #pragma warning(pop)
#endif

class UOrbbecCameraController::FOrbbecImplementation
{
public:
	static TUniquePtr<FOrbbecImplementation> CreateAndStart(
		const FString& DeviceSerialNumber, 
		const TArray<FOrbbecVideoConfig>& VideoConfigs)
	{
		auto Device = PickDevice(DeviceSerialNumber);
		
		if (!Device)
		{
			return nullptr;
		}
		
		TUniquePtr<FOrbbecImplementation> Implementation{ new FOrbbecImplementation(Device) };
		
		for (const FOrbbecVideoConfig& Config : VideoConfigs)
		{
			if (!Implementation->EnableStreamProfile(Config))
			{
				return nullptr;
			}
		}
		
		Implementation->Pipeline.start();
		
		return Implementation;
	}
	
	~FOrbbecImplementation()
	{
		Pipeline.stop();
	}
	
	static OBFormat MapFormat(const EOrbbecFrameFormat Format)
	{
		switch (Format)
		{
		case EOrbbecFrameFormat::YUYV: return OB_FORMAT_YUYV;
		case EOrbbecFrameFormat::MJPG: return OB_FORMAT_MJPG;
		case EOrbbecFrameFormat::Y16:  return OB_FORMAT_Y16;
		case EOrbbecFrameFormat::RGB:  return OB_FORMAT_RGB;
		case EOrbbecFrameFormat::BGR:  return OB_FORMAT_BGR;
		case EOrbbecFrameFormat::BGRA: return OB_FORMAT_BGRA;
		case EOrbbecFrameFormat::RGBA: return OB_FORMAT_RGBA;
		default: return OB_FORMAT_UNKNOWN;
		}
	}

	static EOrbbecFrameFormat MapFormatBack(const OBFormat Format)
	{
		switch (Format)
		{
		case OB_FORMAT_YUYV: return EOrbbecFrameFormat::YUYV;
		case OB_FORMAT_MJPG: return EOrbbecFrameFormat::MJPG;
		case OB_FORMAT_Y16:  return EOrbbecFrameFormat::Y16;
		case OB_FORMAT_RGB:  return EOrbbecFrameFormat::RGB;
		case OB_FORMAT_BGR:  return EOrbbecFrameFormat::BGR;
		case OB_FORMAT_BGRA: return EOrbbecFrameFormat::BGRA;
		case OB_FORMAT_RGBA: return EOrbbecFrameFormat::RGBA;
		default: return EOrbbecFrameFormat::Unknown;
		}
	}
	
	static OBSensorType MapSensorType(const EOrbbecSensorType StreamType)
	{
		switch (StreamType)
		{
		case EOrbbecSensorType::IR: return OB_SENSOR_IR;
		case EOrbbecSensorType::Color: return OB_SENSOR_COLOR;
		case EOrbbecSensorType::Depth: return OB_SENSOR_DEPTH;
		case EOrbbecSensorType::IRLeft: return OB_SENSOR_IR_LEFT;
		case EOrbbecSensorType::IRRight: return OB_SENSOR_IR_RIGHT;
		case EOrbbecSensorType::ColorLeft: return OB_SENSOR_COLOR_LEFT;
		case EOrbbecSensorType::ColorRight: return OB_SENSOR_COLOR_RIGHT;
		default: return OB_SENSOR_UNKNOWN;
		}
	}
	
	static EOrbbecSensorType MapSensorTypeBack(const OBSensorType StreamType)
	{
		switch (StreamType)
		{
		case OB_SENSOR_IR: return EOrbbecSensorType::IR;
		case OB_SENSOR_COLOR: return EOrbbecSensorType::Color;
		case OB_SENSOR_DEPTH: return EOrbbecSensorType::Depth;
		case OB_SENSOR_IR_LEFT: return EOrbbecSensorType::IRLeft;
		case OB_SENSOR_IR_RIGHT: return EOrbbecSensorType::IRRight;
		case OB_SENSOR_COLOR_LEFT: return EOrbbecSensorType::ColorLeft;
		case OB_SENSOR_COLOR_RIGHT: return EOrbbecSensorType::ColorRight;
		default: return EOrbbecSensorType::Unknown;
		}
	}
	
private:
	ob::Pipeline Pipeline;
	ob::Config Config;
	
	explicit FOrbbecImplementation(std::shared_ptr<ob::Device> Device) : Pipeline(Device) {}
	
	static std::shared_ptr<ob::Device> PickDevice(const FString& DeviceSerialNumber)
	{
		const ob::Context Ctx;
		const auto DevList = Ctx.queryDeviceList();
		const auto DevCount = DevList->deviceCount();
		
		if (DevCount <= 0) {
			UE_LOG(LogOrbbecSensor, Warning, TEXT("No Orbbec devices detected (deviceCount == 0)."));
			return nullptr;
		}

		// Default: first device
		if (DeviceSerialNumber.IsEmpty()) {
			return DevList->getDevice(0);
		}
		
		// SN provided: find it if possible
		for (uint32_t i = 0; i < DevCount; ++i)
		{
			auto Device = DevList->getDevice(i);
			
			if (const auto Info = Device->getDeviceInfo(); DeviceSerialNumber == Info->serialNumber())
			{
				return Device;
			}
		}
		
		// Help the user find the device by serial number
		UE_LOG(
			LogOrbbecSensor, 
			Warning, 
			TEXT("No Orbbec device with serial number '%s' detected. We see these devices:"), 
			*DeviceSerialNumber);
		
		for (uint32_t i = 0; i < DevCount; ++i)
		{
			auto Device = DevList->getDevice(i);
			
			if (const auto Info = Device->getDeviceInfo(); Info->serialNumber())
			{
				UE_LOG(LogOrbbecSensor, Warning, TEXT("  [%d] %s"), i, ANSI_TO_TCHAR(Info->serialNumber()));
			}
		}
		
		return nullptr;
	}
	
	bool EnableStreamProfile(const FOrbbecVideoConfig& VideoConfig) const
	{
		const auto StreamType = MapSensorType(VideoConfig.SensorType);
		const auto Profiles = Pipeline.getStreamProfileList(StreamType);
		
		for (uint32_t i = 0; i < Profiles->count(); ++i)
		{
			const auto Profile = Profiles->getProfile(i);
			const auto VideoProfile = Profile->as<ob::VideoStreamProfile>();
			
			if (!VideoProfile)
			{
				continue;
			}
			
			const bool bIsSameFormat = VideoProfile->getFormat() == MapFormat(VideoConfig.Format);
			const bool bIsSameResolution = 
				VideoProfile->getWidth() == VideoConfig.Width 
				&& VideoProfile->getHeight() == VideoConfig.Height;
			const bool bIsSameFramerate = VideoProfile->getFps() == VideoConfig.Framerate;
			
			if (bIsSameFormat && bIsSameResolution && bIsSameFramerate)
			{
				Config.enableStream(Profile);
				return true;
			}
		}
		
		return false;
	}
};

UOrbbecCameraController::UOrbbecCameraController()
{
}

UOrbbecCameraController::~UOrbbecCameraController()
{
	StopCamera();
}

UOrbbecCameraController::UOrbbecCameraController(FVTableHelper& Helper)
	: Super(Helper)
{
}

bool UOrbbecCameraController::StartCamera()
{
	if (Implementation)
	{
		UE_LOG(LogOrbbecSensor, Display, TEXT("Camera already started. Stopping it first."));
		StopCamera();
	}
	
	try
	{
		Implementation = FOrbbecImplementation::CreateAndStart(DeviceSerialNumber, VideoConfigs);
		
		if (!Implementation)
		{
			return false;
		}
		
		return true;
	}
	catch (const ob::Error& e)
	{
		UE_LOG(LogTemp, Error, TEXT("OrbbecSDK Error during StartCamera(): %s"), *FString(e.getMessage()));
		return false;
	}
}

void UOrbbecCameraController::StopCamera()
{
	
	if (Implementation)
	{
		try
		{
			Implementation.Reset();
		}
		catch (const ob::Error& e)
		{
			UE_LOG(LogTemp, Warning, TEXT("OrbbecSDK Error during StopCamera(): %s"), *FString(e.getMessage()));
		}
	}
}
