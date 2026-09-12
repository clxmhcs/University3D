using System;
using System.Runtime.InteropServices;
using UnityEngine;

namespace JiangchengUniversity.Bridge
{
    public sealed class CampusBridge : MonoBehaviour
    {
        public const int ProtocolVersion = 1;
        public static CampusBridge Instance { get; private set; }

#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")]
        private static extern void CampusBridge_SendToSwift(string json);
#endif

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            gameObject.name = "CampusBridge";
            DontDestroyOnLoad(gameObject);
        }

        public void ReceiveFromNative(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
            {
                Debug.LogWarning("[CampusBridge] Empty native message.");
                return;
            }

            var message = JsonUtility.FromJson<BridgeMessage>(json);
            if (message == null || message.protocolVersion != ProtocolVersion)
            {
                Debug.LogError("[CampusBridge] Protocol mismatch or invalid payload.");
                return;
            }

            switch (message.type)
            {
                case "focusObject":
                    Debug.Log($"[CampusBridge] focusObject({message.objectID})");
                    EmitObjectSelected(message.objectID);
                    break;

                default:
                    Debug.LogWarning($"[CampusBridge] Unsupported message type: {message.type}");
                    break;
            }
        }

        public void EmitObjectSelected(string objectID)
        {
            SendToSwift(new BridgeMessage
            {
                protocolVersion = ProtocolVersion,
                type = "objectSelected",
                objectID = objectID
            });
        }

        private static void SendToSwift(BridgeMessage message)
        {
            var json = JsonUtility.ToJson(message);

#if UNITY_IOS && !UNITY_EDITOR
            CampusBridge_SendToSwift(json);
#else
            Debug.Log($"[CampusBridge][Unity→Swift placeholder] {json}");
#endif
        }
    }
}
