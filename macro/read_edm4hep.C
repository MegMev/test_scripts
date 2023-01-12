#include "podio/ROOTReader.h"
#include "podio/EventStore.h"
#include "DD4hep/Detector.h"
#include "DDRec/CellIDPositionConverter.h"
#include "DD4hep/BitFieldCoder.h"
#include "DD4hep/Objects.h"
#include "DDTest.h"

using namespace dd4hep;

static DDTest test( "edm4hep I/O" ) ; 

//=============================================================================

const double epsilon = dd4hep::micrometer ;
const int maxHit = 100 ;


double dist( const Position& p0, const Position& p1 ){
  Position p2 = p1 - p0 ;
  return p2.r() ;
}

void read_edm4hep()
{
  //
  std::string rest_path(getenv("REST_PATH"));
  std::string geoFile(rest_path+"/geometry/compact/Megat.xml");
  auto& description = dd4hep::Detector::getInstance();
  description.fromXML(geoFile);

  // get the coverter and decoder
  dd4hep::rec::CellIDPositionConverter idposConv( description );
  auto idspec = description.idSpecification("CztHits");
  auto decoder = idspec.decoder();

  //// specify a cell id based on field values
  // method1
  Long64_t tid=0;
  decoder->set(tid, "system", 2);
  decoder->set(tid, "section", 1);
  decoder->set(tid, "layer", 0);
  decoder->set(tid, "row", 13);
  decoder->set(tid, "column", 14);
  decoder->set(tid, "x", 0);
  decoder->set(tid, "y", 0);

  // method2
  typedef std::vector<std::pair<std::string, int>> FieldValues;
  FieldValues field_values = 
    {
      {"system", 2}, 
      { "section", 1 },
      { "layer", 0 },
      { "row", 13 },
      { "column", 14 },
      { "x", 0 },
      { "y", 0 }
    };
  Long64_t tid2=idspec.encode(field_values);
  std::stringstream sst ;
  sst << " compare target ids: " <<  tid << "  -  " << tid2;
  test( tid, tid2,  sst.str() ) ;

  //
  auto h1 = new TH1F("h1","h1",500 , -10,40);
  auto h2 = new TH1F("h2","Contributione Size",100 , -0.5,99.5);
  auto h3 = new TH1F("h3","Edep - Etot",100 , -4.5,5.5);
  auto h4 = new TH1F("h4","MCParticle Contributions Size",100 , -0.5,99.5);
  auto h5 = new TH1F("h5","Eenery Combined",500 , 0, 50);
  auto h6 = new TH1F("h6","Theta",100 , 0, 4);
  auto h7 = new TH1F("h7","Phi",100 , -4, 4);

  // setup edm4hep reader and event store
  podio::ROOTReader reader;
  reader.openFile("../data/megat.edm4hep.root");
  auto store = podio::EventStore();
  store.setReader(&reader);

  //// get id spec from collection metadata
  auto& hits = store.get<edm4hep::SimCalorimeterHitCollection>("CztHits");
  auto& colMD = store.getCollectionMetaData(hits.getID());
  std::cout << "collection metadata:\n" << colMD.getValue<std::string>("CellIDEncodingString") << std::endl;
  IDDescriptor idspec_test("CztHits", colMD.getValue<std::string>("CellIDEncodingString"));
  std::cout << idspec_test.fieldDescription() << std::endl;
  
  unsigned nEvents = reader.getEntries();
  for (unsigned i = 0; i < nEvents; ++i) {
    if(i % 100 == 0)
      std::cout << "reading event " << i << std::endl;

    auto& schs = store.get<edm4hep::SimCalorimeterHitCollection>("CztHits");
    for(auto hit: schs)
      {
        auto cellid = hit.getCellID();
        auto pos = hit.getPosition(); // in mm
        auto energy = hit.getEnergy(); // in GeV

        //
        Position point(pos.x, pos.y, pos.z);
        DetElement det = idposConv.findDetElement( point ) ;

        //// cell id test
        auto id_converted = idposConv.cellID(point);
        // std::stringstream sst ;
        // sst << " compare ids: " << det.name() << " " <<  decoder->valueString(cellid) << "  -  " <<
        //   decoder->valueString(id_converted);
        // test( cellid, id_converted,  sst.str() ) ;

        //// hit position test
        Position point_converted = idposConv.position(cellid);
        // double d = dist(point, point_converted);
        // std::stringstream sst1 ;
        // sst1 << " dist " << d << " ( " <<  point << " ) - ( " << point_converted << " )  - detElement: "
        //      << det.name() ;
        // test( d < epsilon , true  , sst1.str()  ) ;

        //// check single field
        // if(decoder->get(cellid, "y") == 0) // method1
        // if(idspec.field("y")->value(cellid) == 0) // method2
          // std::cout << decoder->valueString(cellid) << " (" << id_converted<<")"<<std::endl;

        //// fill histograms
        h1->Fill(1000*energy);
        h6->Fill(point.theta());
        h7->Fill(point.phi());

        //// MC controbutions
        double etotal=0;
        std::map<unsigned int,edm4hep::MCParticle> mpids;
        std::map<edm4hep::MCParticle, unsigned int> mpids_rev;
        //// method1
        for(auto contrib: hit.getContributions()) {
          etotal += contrib.getEnergy();
          //
          auto mp = contrib.getParticle();
          auto id = mp.id();
          if(mpids.find(id) == mpids.end()) 
            {
              mpids[id] = mp;
              // std::cout << "Same particle " << mp << std::endl;
            }
          if(mpids_rev.find(mp) == mpids_rev.end())
            mpids_rev[mp]=id;
        }
        //// method2
        // for(auto it=hit.contributions_begin();it!=hit.contributions_end();++it)
        //   {
        //     etotal += it->getEnergy();
        //   }
        
        if (mpids.size() != mpids_rev.size())
          std::cout << "Error: unmatched mc particles" << std::endl;
        h2->Fill(hit.contributions_size());
        h4->Fill(mpids.size());
        h3->Fill(energy-etotal);
      }
    
    //// other looping methods
    // for (int j=0, end=schs.size(); j != end; ++j)
    //   {
    //     h1->Fill(1000*schs[j].getEnergy());
    //   }
    //    for(auto hit=schs.begin(), end=schs.end(); hit != end; ++hit) 
            // {
            //   h1->Fill(1000*hit->getEnergy());
            // }

            auto edeps = schs.energy();
    if(edeps.size())
      h5->Fill(1000*std::reduce(edeps.cbegin(), edeps.cend()));
    
    // prepare next event
    store.clear();
    reader.endOfEvent();
  }
  reader.closeFile();

  auto c = new TCanvas("c","c",1000,350);
  c->Divide(3,1);
  c->cd(1);
  h1->Draw();
  c->cd(2);
  h2->Draw();
  c->cd(3);
  h7->Draw();

  auto c2 = new TCanvas("c2","",1000,350);
  c2->Divide(3,1);
  c2->cd(1);
  h5->Draw();
  c2->cd(2);
  h4->Draw();
  c2->cd(3);
  h6->Draw();
}
