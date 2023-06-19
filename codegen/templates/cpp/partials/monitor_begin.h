
int monitor(Inputs &inputs) {

  std::vector<std::unique_ptr<Trace<TraceEvent>>> traces;
  std::vector<InputStream *> online_traces;

  using WorkbagTy = Workbag<ConfigurationsSetTy>;
  WorkbagTy workbag;
  WorkbagTy new_workbag;

#define STATS
#ifdef STATS
  // Stats stats;
  size_t max_wbg_size = 0;
  // size_t tuples_num = 0;
#endif

  while (true) {
    /////////////////////////////////
    /// UPDATE TRACES (NEW TRACES AND NEW EVENTS)
    /////////////////////////////////

    update_traces(inputs, workbag, traces, online_traces);

    /////////////////////////////////
    /// MOVE TRANSDUCERS
    /////////////////////////////////

    size_t wbg_size = workbag.size();
    size_t wbg_invalid = 0;
#ifdef STATS
    max_wbg_size = std::max(wbg_size, max_wbg_size);
#endif
#ifdef DEBUG
    std::cout << "WORKBAG size: " << wbg_size << "\n";
#endif