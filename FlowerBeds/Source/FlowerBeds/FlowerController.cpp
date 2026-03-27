#include "FlowerController.h"

#include "OSCClient.h"
#include "OSCManager.h"

void UFlowerController::Init(const FFlowerControllerConfig& Config)
{
	OscClient = UOSCManager::CreateOSCClient(
		Config.IPAddress,
		Config.Port,
		"FlowerControllerOSCClient",
		this);
}

void UFlowerController::SendFlowerRotation(const uint8 MotorId, float Rotation) const
{
	const FOSCAddress FlowerRotationAddress(FlowerRotationOSCAddress);
	UE::OSC::FOSCData MotorIdData(MotorId);
	UE::OSC::FOSCData RotationData(Rotation);
	FOSCMessage Message(FlowerRotationAddress, { MotorIdData, RotationData });
	OscClient->SendOSCMessage(Message);
}
