using System;

namespace JiangchengUniversity.Bridge
{
    [Serializable]
    public sealed class BridgeMessage
    {
        public int protocolVersion = 1;
        public string type;
        public string objectID;
        public string payloadJson;
    }
}
