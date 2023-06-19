  }

  if (!new_workbag.empty() || wbg_invalid >= wbg_size / 3) {
    for (auto &C : workbag) {
      if (C.invalid())
        continue;
      new_workbag.push(std::move(C));
    }
    workbag.swap(new_workbag);
    new_workbag.clear();
  }

  /////////////////////////////////

    if (workbag.empty() && inputs.done()) {
    #ifdef OUTPUT
      std::cout << "No more traces to come, workbag empty\n";
      std::cout << "\033[1;32mNO VIOLATION FOUND!\033[0m\n";
    #endif
      break;
    }
  }

  #ifdef STATS
  std::cout << "Max workbag size: " << max_wbg_size << "\n";
  std::cout << "Traces #: " << traces.size() << "\n";
  #endif

  return 0;

  violated :
  #ifdef STATS
      std::cout
      << "Max workbag size: "
      << max_wbg_size
      << "\n";
  std::cout << "Traces #: " << traces.size() << "\n";
  #endif
  return 1;
  }