#include <iostream>
#include <vector>
#include <unordered_set>
#include <algorithm>

#include "../Common/Peer.hpp"
#include "DolevPeer.hpp"

using namespace std;

namespace quantas {

    inline double getAvgDeliveryRound(const vector<Peer *> &peers) {
        int cntDelivered = 0;
        int cntDeliveredRound = 0;
        for (Peer *peerPtr : peers) {
            if (auto *dolevpeer = dynamic_cast<DolevPeer *>(peerPtr)) {
                if (dolevpeer->delivered) {
                    cntDelivered++;
                    cntDeliveredRound += dolevpeer->deliveryRound;
                }
            }
        }
        double avgDeliveredRound = 0.0;
        if (cntDelivered > 0) {
            avgDeliveredRound = static_cast<double>(cntDeliveredRound) / cntDelivered;
        }
        return avgDeliveredRound;
    }

    inline double getAvgCorrectNodeDelivered(const vector<Peer *> &peers) {
        int cntCorrectDelivered = 0;
        int cntCorrect = 0;
        for (Peer *peerPtr : peers) {
            if (auto *dolevpeer = dynamic_cast<DolevPeer *>(peerPtr)) {
                if (!dolevpeer->isByzantine) {
                    cntCorrect++;
                    if (dolevpeer->delivered) {
                        cntCorrectDelivered++;
                    }
                }
            }
        }
        double avgCorrectDelivered = 0.0;
        if (cntCorrect > 0) {
            avgCorrectDelivered = static_cast<double>(cntCorrectDelivered) / cntCorrect;
            avgCorrectDelivered *= 100.0; // convert to percentage
            avgCorrectDelivered = round(avgCorrectDelivered * 100.0) / 100.0; // round to 2 decimal places
        }
        return avgCorrectDelivered;
    }

    inline int getTotalMessagesSent(const vector<Peer *> &peers) {
        int total = 0;
        for (Peer *peerPtr : peers) {
            if (auto *dolevpeer = dynamic_cast<DolevPeer *>(peerPtr)) {
                total += dolevpeer->msgsSent;
            }
        }
        return total;
    }

    inline double getAvgMessagesSent(const vector<Peer *> &peers) {
        int total = getTotalMessagesSent(peers);
        int correctNodes = 0;
        for (Peer *peerPtr : peers) {
            if (auto *dolevpeer = dynamic_cast<DolevPeer *>(peerPtr)) {
                if (!dolevpeer->isByzantine) {
                    correctNodes++;
                }
            }
        }
        double avg = 0.0;
        if (correctNodes > 0) {
            avg = static_cast<double>(total) / correctNodes;
            avg = round(avg * 100.0) / 100.0; // round to 2 decimal places
        }
        return avg;
    }

    inline json saveResults(const vector<Peer *> &peers) {
        double avgDeliveryRound = getAvgDeliveryRound(peers);
        double avgCorrectNodeDelivered = getAvgCorrectNodeDelivered(peers);
        int totalMessagesSent = getTotalMessagesSent(peers);
        double avgMessagesSent = getAvgMessagesSent(peers);

        //cout << "Average Delivery Round: " << avgDeliveryRound << endl;
        //cout << "Average Correct Node Delivered: " << avgCorrectNodeDelivered << "%" << endl;
        //cout << "Total Messages Sent: " << totalMessagesSent << endl;
        //cout << "Average Messages Sent by Correct Nodes: " << avgMessagesSent << endl;
        return {{"avgDeliveryRound", avgDeliveryRound},
                {"avgCorrectNodeDelivered", avgCorrectNodeDelivered},
                {"totalMessagesSent", totalMessagesSent},
                {"avgMessagesSent", avgMessagesSent}};
    }
}