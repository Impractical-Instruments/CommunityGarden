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
	static TSharedPtr<FOrbbecImplementation> CreateAndStart(
		const FString& DeviceSerialNumber, 
		const FOrbbecVideoConfig& ColorConfig,
		const FOrbbecVideoConfig& DepthConfig,
		const FOrbbecVideoConfig& IRConfig)
	{
		auto Device = PickDevice(DeviceSerialNumber);
		
		if (!Device)
		{
			return nullptr;
		}
		
		TSharedPtr<FOrbbecImplementation> Implementation{ new FOrbbecImplementation(Device) };
		
		if (!Implementation->EnableStreamProfile(EOrbbecSensorType::Color, ColorConfig)) return nullptr;
		if (!Implementation->EnableStreamProfile(EOrbbecSensorType::Depth, DepthConfig)) return nullptr;
		if (!Implementation->EnableStreamProfile(EOrbbecSensorType::IR, IRConfig)) return nullptr;
		
		Implementation->Pipeline.start(
			Implementation->Config, 
			[WeakThis = Implementation.ToWeakPtr()](std::shared_ptr<ob::FrameSet> FrameSet)
			{
				if (const auto SharedThis = WeakThis.Pin())
				{
					SharedThis->HandleFrameSet(std::move(FrameSet));
				}
			});
		
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
		default: return EOrbbecSensorType::Unknown;
		}
	}
	
	bool TryConsumeLatestFrameSet(FOrbbecFrame& ColorFrame, FOrbbecFrame& DepthFrame, FOrbbecFrame& IRFrame)
	{
		std::shared_ptr<ob::FrameSet> OutFrameSet;
		
		// Get the latest frame set, if available
		{
			FScopeLock Lock(&LatestFrameSetGuard);
		
			if (!LatestFrameSet)
			{
				return false;
			}
		
			OutFrameSet = LatestFrameSet;
			LatestFrameSet.reset();
		}
		
		if (ColorFrame.Config.bEnabled)
		{
			const auto Frame = OutFrameSet->getColorFrame();
			ensure(ColorFrame.Config.Format == MapFormatBack(Frame->getFormat()));
			const auto DataSize = Frame->getDataSize();
			ColorFrame.Data.SetNumUninitialized(DataSize);
			FMemory::Memcpy(ColorFrame.Data.GetData(), Frame->getData(), DataSize);
		}
		if (DepthFrame.Config.bEnabled)
		{
			const auto Frame = OutFrameSet->getDepthFrame();
			ensure(DepthFrame.Config.Format == MapFormatBack(Frame->getFormat()));
			const auto DataSize = Frame->getDataSize();
			DepthFrame.Data.SetNumUninitialized(DataSize);
			FMemory::Memcpy(DepthFrame.Data.GetData(), Frame->getData(), DataSize);
		}
		if (IRFrame.Config.bEnabled)
		{
			const auto Frame = OutFrameSet->getIrFrame();
			ensure(IRFrame.Config.Format == MapFormatBack(Frame->getFormat()));
			const auto DataSize = Frame->getDataSize();
			IRFrame.Data.SetNumUninitialized(DataSize);
			FMemory::Memcpy(IRFrame.Data.GetData(), Frame->getData(), DataSize);
		}
		
		return true;
	}
	
private:
	ob::Pipeline Pipeline;
	std::shared_ptr<ob::Config> Config = std::make_shared<ob::Config>();
	
	FCriticalSection LatestFrameSetGuard;
	std::shared_ptr<ob::FrameSet> LatestFrameSet;
	
	explicit FOrbbecImplementation(std::shared_ptr<ob::Device> Device) : Pipeline(std::move(Device)) {}
	
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
	
	bool EnableStreamProfile(const EOrbbecSensorType SensorType, const FOrbbecVideoConfig& VideoConfig) const
	{
		// Skip if not enabled
		if (!VideoConfig.bEnabled)
		{
			return true;
		}
		
		const auto ObSensorType = MapSensorType(SensorType);
		const auto Profiles = Pipeline.getStreamProfileList(ObSensorType);
		
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
				Config->enableStream(Profile);
				return true;
			}
		}
		
		return false;
	}
	
	void HandleFrameSet(std::shared_ptr<ob::FrameSet> FrameSet)
	{
		FScopeLock Lock(&LatestFrameSetGuard);
		LatestFrameSet = std::move(FrameSet);
	}
};

UOrbbecCameraController::UOrbbecCameraController()
{
	PrimaryComponentTick.bCanEverTick = true;
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
		Implementation = FOrbbecImplementation::CreateAndStart(DeviceSerialNumber, ColorConfig, DepthConfig, IRConfig);
		
		if (!Implementation)
		{
			return false;
		}
		
		// Init the latest frames
		LatestColorFrame.Config = ColorConfig;
		LatestDepthFrame.Config = DepthConfig;
		LatestIRFrame.Config = IRConfig;
		
		// Turn on ticks so we can receive frames
		SetComponentTickEnabled(true);
		
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
	SetComponentTickEnabled(false);
	
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

void UOrbbecCameraController::TickComponent(
	const float DeltaTime, 
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	
	if (!Implementation)
	{
		return;
	}
	
	if (OnFramesReceived.IsBound())
	{
		if (Implementation->TryConsumeLatestFrameSet(LatestColorFrame, LatestDepthFrame, LatestIRFrame))
		{
			OnFramesReceived.Broadcast(LatestColorFrame, LatestDepthFrame, LatestIRFrame);
		}
	}
}
